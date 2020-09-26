import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Set, Tuple, Union, cast

from asyncpg import Connection, Record

from libcard2 import string_mgr

from . import lang_specific
import base64

Timespan = Tuple[datetime, timedelta]


@dataclass
class SEventRecord(object):
    record_id: int
    server_id: str
    common_title: str
    feature_card_ids: Set[int]
    thumbnail: str
    time_span: Timespan

    def get_dedup_timespan(self):
        return (*self.time_span, tuple(sorted(self.feature_card_ids)))

    def get_full_range(self):
        return (self.time_span[0], self.time_span[0] + self.time_span[1])


@dataclass
class SGachaMergeRecord(object):
    T_EVENT_TIE = 1
    T_PICK_UP = 2
    T_FES = 3
    T_ELSE = 4
    T_IGNORE = -1

    record_id: int
    server_id: str
    common_title: str
    feature_card_ids: Dict[int, str]
    maybe_type: int
    thumbnail: str
    time_spans: Dict[str, Timespan] = field(default_factory=dict)

    def get_dedup_timespan(self):
        return (*self.time_spans["gacha"], tuple(sorted(self.feature_card_ids.keys())))

    def get_full_range(self):
        if "part2" not in self.time_spans:
            return (
                self.time_spans["gacha"][0],
                self.time_spans["gacha"][0] + self.time_spans["gacha"][1],
            )

        s = min(self.time_spans["gacha"][0], self.time_spans["part2"][0])
        e = max(
            self.time_spans["gacha"][0] + self.time_spans["gacha"][1],
            self.time_spans["part2"][0] + self.time_spans["part2"][1],
        )
        return (s, e)


AnySRecord = Union[SGachaMergeRecord, SEventRecord]
DateMinedNewsItem = Tuple[Record, Iterable[datetime]]


def get_time(tstag: str) -> datetime:
    m = re.match(".*v:([0-9]+)", tstag)
    if not m:
        raise ValueError("invalid ts annotation")
    return datetime.utcfromtimestamp(int(m.group(1)))


def deduplicate_srecords(spans: Iterable[AnySRecord]) -> List[AnySRecord]:
    dedup: Dict[Timespan, AnySRecord] = {}
    for record in spans:
        eff_ts = record.get_dedup_timespan()
        have_record = dedup.get(eff_ts)
        if not have_record or have_record.record_id > record.record_id:
            dedup[eff_ts] = record
        else:
            logging.debug("Suppressing supposed duplicate record: %s.", record)

    return sorted(dedup.values(), key=lambda x: x.get_dedup_timespan())


def make_spans(record_list: Iterable[Record]) -> Iterable[DateMinedNewsItem]:
    cr_id = None
    cr_rec = None
    cr_tspan: List[datetime] = []
    for record in record_list:
        if lang_specific.is_postscript(record):
            logging.debug("Suppressing postscripted record: %s", record["title"])
            continue

        if cr_id != record["news_id"]:
            if len(cr_tspan) >= 2:
                yield (cr_rec, cr_tspan)
            cr_rec = record
            cr_tspan = []
            cr_id = record["news_id"]

        cr_tspan.append(get_time(record["regexp_matches"][0]))

    if len(cr_tspan) >= 2:
        yield (cr_rec, cr_tspan)


def merge_gachas(tag, gachas: Iterable[DateMinedNewsItem]):
    def window(itr):
        try:
            first = next(itr)
        except StopIteration:
            return

        second = None
        for second in itr:
            yield (first, second)
            first = second
        if second:
            yield (second, (None, None))

    cleanup_func = lang_specific.get_name_clean_func(tag)

    buf: Optional[SGachaMergeRecord] = None
    for (sp1_record, sp1_timestamps), (sp2_record, sp2_timestamps) in window(iter(gachas)):
        tagger = lang_specific.get_gacha_label_func(tag)
        gtype = tagger(sp1_record["title"])

        if gtype == SGachaMergeRecord.T_EVENT_TIE:
            # Event tie-in. This is a bit complicated since there is a combined post, then
            # extra posts for part 1 and 2.
            if len(sp1_timestamps) >= 4:
                fh_start, fh_end, sh_start, sh_end = sp1_timestamps[:4]
                dates = {
                    "gacha": (fh_start, fh_end - fh_start),
                    "part2": (sh_start, sh_end - sh_start),
                }
                card_refs = {id: "gacha" for id in json.loads(sp1_record["card_refs"])}

                if buf:
                    if card_refs == buf.feature_card_ids:
                        continue
                    logging.debug("Yielding: %s", buf)
                    yield buf

                # If this is the combined post, build the merge entry with it. We need to
                # save it because we will be borrowing the banner from the first-half post.
                buf = SGachaMergeRecord(
                    sp1_record["news_id"],
                    tag,
                    cleanup_func(1, sp1_record["title"]),
                    card_refs,
                    gtype,
                    sp1_record["thumbnail"],
                    dates,
                )
                logging.debug("Buffered an omnibus news post for %s.", sp1_record["title"])
            else:
                # This is the post for the first half. If there's something buffered,
                # hopefully it's the combined merge record. If it is, attach the thumbnail.
                # But since the buffer only holds one, we need to send it on its way either way.
                card_refs = {id: "gacha" for id in json.loads(sp1_record["card_refs"])}
                mentioned_cids_p1 = set(card_refs.keys())

                if sp2_record:
                    next_card_refs = {id: "gachap2" for id in json.loads(sp2_record["card_refs"])}
                    have_part2 = bool(set(next_card_refs.keys()) & mentioned_cids_p1)
                else:
                    have_part2 = False

                use_id = sp1_record["news_id"]

                if buf:
                    if set(buf.feature_card_ids.keys()) >= mentioned_cids_p1:
                        if not have_part2:
                            buf.thumbnail = sp1_record["thumbnail"]
                            logging.debug("Yielding same w/ attached thumb: %s", buf)
                            yield buf
                            buf = None
                            continue
                        logging.warning("Deleting buffered post %s to use part1/part2 posts.", buf)

                        # Steal the lineup ID since it's posted earliest.
                        use_id = buf.record_id
                        buf = None
                    else:
                        logging.warning("Kicking out buffered post %s for non-matching entry", buf)
                        yield buf
                        buf = None

                # For some reason there wasn't a merge record for this, so do the best we can.
                # Hopefully the part 2 post is in sp2.
                rec = SGachaMergeRecord(
                    use_id,
                    tag,
                    cleanup_func(1, sp1_record["title"]),
                    card_refs,
                    gtype,
                    sp1_record["thumbnail"],
                    {"gacha": (sp1_timestamps[0], sp1_timestamps[1] - sp1_timestamps[0])},
                )

                if have_part2:
                    # Merge.
                    rec.feature_card_ids = next_card_refs
                    rec.feature_card_ids.update(card_refs)
                    rec.time_spans["part2"] = (
                        sp2_timestamps[0],
                        sp2_timestamps[1] - sp2_timestamps[0],
                    )

                # Else:
                # Usually the event gachas have the SR in common. If not, that's suspicious...
                # Discard the sp2 post then. If it's for a different banner, it will get a
                # second chance when it moves into sp1.

                logging.warning("Yielding post with no line-up preceding: %s.", rec.common_title)
                yield rec
        elif gtype == SGachaMergeRecord.T_IGNORE:
            continue
        else:
            if buf:
                yield buf
                buf = None

            # Regular gachas are just single posts and we can pass them though. Phew.
            sp1_start, sp1_end = sp1_timestamps[:2]
            ctspan = (sp1_start, sp1_end - sp1_start)

            logging.debug("Yielding fes or pickup: %s.", sp1_record["title"])
            yield SGachaMergeRecord(
                sp1_record["news_id"],
                tag,
                cleanup_func(1, sp1_record["title"]),
                {id: "gacha" for id in json.loads(sp1_record["card_refs"])},
                gtype,
                sp1_record["thumbnail"],
                {"gacha": ctspan},
            )

    if buf:
        logging.debug("Yielding leftover: %s.", buf.common_title)
        yield buf


OK_TO_MERGE = [SGachaMergeRecord.T_EVENT_TIE, SGachaMergeRecord.T_ELSE]


def take_event(fromlist, start, matching) -> Optional[int]:
    end = len(fromlist)
    while start < end:
        r = fromlist[start]
        if not isinstance(r, SEventRecord):
            start += 1
            continue

        fr = r.get_full_range()
        if (fr[0] >= matching[0] and fr[0] < matching[1]) or (
            fr[1] > matching[0] and fr[1] <= matching[1]
        ):
            return start
        start += 1

    return None


def take_gacha(fromlist, start, matching) -> Optional[int]:
    end = len(fromlist)
    while start < end:
        r = fromlist[start]
        if not isinstance(r, SGachaMergeRecord) or r.maybe_type not in OK_TO_MERGE:
            start += 1
            continue

        fr = r.get_full_range()
        if (fr[0] >= matching[0] and fr[0] < matching[1]) or (
            fr[1] > matching[0] and fr[1] <= matching[1]
        ):
            return start
        start += 1

    return None


def zip_records(events: List[AnySRecord], gachas: List[AnySRecord]):
    serial = gachas + events
    serial.sort(key=lambda x: x.get_dedup_timespan())
    i = 0
    end = len(serial)

    l_out: List[AnySRecord] = []
    while i < end:
        r = serial[i]
        if isinstance(r, SGachaMergeRecord) and r.maybe_type in OK_TO_MERGE:
            evt_i = take_event(serial, i, r.get_full_range())
            if evt_i is None:
                l_out.append(r)
                i += 1
                continue

            cor_event = cast(SEventRecord, serial.pop(evt_i))
            end -= 1
            logging.debug(
                "Determined that %s is the matching event for %s.",
                cor_event.common_title,
                r.common_title,
            )

            r.common_title = cor_event.common_title
            r.thumbnail = cor_event.thumbnail
            r.feature_card_ids.update({id: "event" for id in cor_event.feature_card_ids})
            r.time_spans["event"] = cor_event.time_span
            r.maybe_type = SGachaMergeRecord.T_EVENT_TIE
            l_out.append(r)
        elif isinstance(r, SEventRecord):
            evt_i = take_gacha(serial, i, r.get_full_range())
            if evt_i is None:
                l_out.append(r)
                i += 1
                continue

            cor_gacha = cast(SGachaMergeRecord, serial.pop(evt_i))
            end -= 1
            logging.debug(
                "Determined that %s is the matching gacha for %s.",
                cor_gacha.common_title,
                r.common_title,
            )

            cor_gacha.common_title = r.common_title
            cor_gacha.thumbnail = r.thumbnail
            cor_gacha.feature_card_ids.update({id: "event" for id in r.feature_card_ids})
            cor_gacha.time_spans["event"] = r.time_span
            cor_gacha.maybe_type = SGachaMergeRecord.T_EVENT_TIE
            l_out.append(r)
        else:
            l_out.append(r)

        i += 1

    return l_out


async def get_replay(connection, tag):
    row = await connection.fetchrow(
        """SELECT news_v2.ts FROM history_v5 INNER JOIN news_v2 
            ON (history_v5.id = news_v2.news_id AND history_v5.serverid = news_v2.serverid)
            WHERE history_v5.serverid=$1
            ORDER BY news_v2.ts DESC LIMIT 1""",
        tag,
    )
    if row:
        return row["ts"]

    return datetime.fromtimestamp(0)


async def assemble_timeline(
    connection: Connection, sid: str
) -> Tuple[List[SEventRecord], List[SGachaMergeRecord]]:
    script = """
    SELECT news_id, internal_category, title, card_refs, thumbnail, 
    regexp_matches(body_html, '<\?asi-blind-ts (.+?)\?>', 'g') 
    FROM news_v2
    WHERE serverid = $1 AND internal_category IN (2, 3) 
    AND card_refs IS NOT NULL AND ts >= $2
    ORDER BY ts
    """

    replay_point = await get_replay(connection, sid)
    logging.debug("NewsMiner: replaying from %s for sid %s", replay_point, sid)

    records = await connection.fetch(script, sid, replay_point)
    logging.debug("NewsMiner: extracting from %d rows", len(records))

    spans = list(make_spans(records))
    spans.sort(key=lambda x: x[1][0])

    cleanup_func = lang_specific.get_name_clean_func(sid)
    event_dmnis = []
    for record, (stime, etime, *_) in spans:
        if record["internal_category"] == 3:
            ctspan = (stime, etime - stime)
            mcids = set(json.loads(record["card_refs"]))
            event_dmnis.append(
                SEventRecord(
                    record["news_id"],
                    sid,
                    cleanup_func(2, record["title"]),
                    mcids,
                    record["thumbnail"],
                    ctspan,
                )
            )

    evt_records = deduplicate_srecords(event_dmnis)
    gacha_records = deduplicate_srecords(
        merge_gachas(sid, (x for x in spans if x[0]["internal_category"] == 2))
    )

    logging.debug(
        "NewsMiner: created %d/%d (evt/gacha) new rows", len(evt_records), len(gacha_records)
    )

    return zip_records(evt_records, gacha_records)


def _jst(y, m, d, h, mm) -> datetime:
    sub = timedelta(hours=9, minutes=0)
    return datetime(y, m, d, h, mm, 0) - sub


def _tspan(t1, t2) -> Timespan:
    return (t1, t2 - t1)


def prepare_old_evt_entries(sid):
    if sid != "jp":
        return [], []

    g_STARS = SGachaMergeRecord(
        4537179,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "素敵なところへご招待！ガチャ開催"),
        {id: "gacha" for id in {301013001, 300082001}},
        SGachaMergeRecord.T_EVENT_TIE,
        base64.b64decode(b"JipD====").decode("utf8"),
        {"gacha": _tspan(_jst(2019, 12, 6, 15, 0), _jst(2019, 12, 16, 14, 59))},
    )
    e_STARS = SEventRecord(
        6462003,
        "jp",
        lang_specific.get_name_clean_func("jp")(2, "ストーリーイベント「素敵なところへご招待！」開催"),
        {400073001, 401022001, 402082001},
        base64.b64decode(b"RUdr====").decode("utf8"),
        _tspan(_jst(2019, 12, 6, 15, 0), _jst(2019, 12, 16, 14, 59)),
    )
    ##
    g_FES_1 = SGachaMergeRecord(
        5874664,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "スクスタフェス開催！！"),
        {id: "gacha" for id in {200063001, 201053001, 202043001, 200032001, 201092001}},
        SGachaMergeRecord.T_FES,
        base64.b64decode(b"VjBy====").decode("utf8"),
        {"gacha": _tspan(_jst(2019, 11, 30, 15, 00), _jst(2019, 12, 6, 14, 59))},
    )
    ##
    g_HIKE = SGachaMergeRecord(
        1594168,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "ハイキングでリフレッシュ！ガチャ開催"),
        {id: "gacha" for id in {300023001, 301062001}},
        SGachaMergeRecord.T_EVENT_TIE,
        base64.b64decode(b"cF5d====").decode("utf8"),
        {"gacha": _tspan(_jst(2019, 11, 21, 15, 00), _jst(2019, 11, 30, 14, 59))},
    )
    e_HIKE = SEventRecord(
        6382193,
        "jp",
        lang_specific.get_name_clean_func("jp")(2, "ストーリーイベント「ハイキングでリフレッシュ！」開催"),
        {401073001, 400042001, 402062001},
        base64.b64decode(b"MWxa====").decode("utf8"),
        _tspan(_jst(2019, 11, 21, 15, 00), _jst(2019, 11, 30, 14, 59)),
    )

    g_PICKUP3 = SGachaMergeRecord(
        -300003,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "ピックアップガチャ開催"),
        {id: "gacha" for id in {300072001, 301023001}},
        SGachaMergeRecord.T_PICK_UP,
        None,
        {"gacha": _tspan(_jst(2019, 11, 15, 15, 00), _jst(2019, 11, 21, 12, 59))},
    )

    g_OLDTOWN = SGachaMergeRecord(
        -200003,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "下町巡り珍道中ガチャ開催"),
        {id: "gacha" for id in {300052001, 301033001}},
        SGachaMergeRecord.T_EVENT_TIE,
        None,
        {"gacha": _tspan(_jst(2019, 11, 6, 15, 00), _jst(2019, 11, 15, 14, 59))},
    )
    e_OLDTOWN = SEventRecord(
        -100003,
        "jp",
        lang_specific.get_name_clean_func("jp")(2, "ストーリーイベント「下町巡り珍道中」開催"),
        {400083001, 401082001, 402052001},
        None,
        _tspan(_jst(2019, 11, 6, 15, 00), _jst(2019, 11, 15, 14, 59)),
    )

    g_PICKUP2 = SGachaMergeRecord(
        -300002,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "ピックアップガチャ開催"),
        {id: "gacha" for id in {300043001, 301072001, 302032001}},
        SGachaMergeRecord.T_PICK_UP,
        None,
        {"gacha": _tspan(_jst(2019, 10, 31, 15, 00), _jst(2019, 11, 6, 12, 59))},
    )
    g_MODELS = SGachaMergeRecord(
        -200002,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "和装モデルはお任せあれ！ガチャ開催"),
        {id: "gacha" for id in {301043001, 300062001}},
        SGachaMergeRecord.T_EVENT_TIE,
        None,
        {"gacha": _tspan(_jst(2019, 10, 21, 15, 00), _jst(2019, 10, 31, 14, 59))},
    )
    e_MODELS = SEventRecord(
        -100002,
        "jp",
        lang_specific.get_name_clean_func("jp")(2, "ストーリーイベント「和装モデルはお任せあれ！」開催"),
        {400092001, 401093001, 402022001},
        None,
        _tspan(_jst(2019, 10, 21, 15, 00), _jst(2019, 10, 31, 14, 59)),
    )

    g_PICKUP1 = SGachaMergeRecord(
        -300001,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "ピックアップガチャ開催"),
        {id: "gacha" for id in {301063001, 300022001}},
        SGachaMergeRecord.T_PICK_UP,
        None,
        {"gacha": _tspan(_jst(2019, 10, 15, 15, 00), _jst(2019, 10, 21, 12, 59))},
    )
    g_SPARTY = SGachaMergeRecord(
        -200001,
        "jp",
        lang_specific.get_name_clean_func("jp")(1, "秘密のパーティ！ガチャ開催"),
        {id: "gacha" for id in {300033001, 301052001}},
        SGachaMergeRecord.T_EVENT_TIE,
        None,
        {"gacha": _tspan(_jst(2019, 9, 30, 15, 00), _jst(2019, 10, 13, 14, 59))},
    )
    e_SPARTY = SEventRecord(
        -100001,
        "jp",
        lang_specific.get_name_clean_func("jp")(2, "ストーリーイベント「秘密のパーティ！」開催"),
        {400013001, 401012001, 402012001},
        None,
        _tspan(_jst(2019, 10, 3, 15, 00), _jst(2019, 10, 15, 14, 59)),
    )

    return zip_records(
        [e_SPARTY, e_MODELS, e_OLDTOWN, e_HIKE, e_STARS],
        [g_SPARTY, g_PICKUP1, g_MODELS, g_PICKUP2, g_OLDTOWN, g_PICKUP3, g_HIKE, g_FES_1, g_STARS],
    )

