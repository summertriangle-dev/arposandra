import sys
import json
import asyncio
from unittest import mock
from datetime import datetime
import logging

from astool import ctx, iceapi

from maintenance.news import ingest
from maintenance.news import dm_parse
from maintenance.news import theatre_parse


DT_DISABLED_REGIONS = {"en"}


def begin_session_2(context):
    # with open("news/test/fetchNotice.json", "r") as mock_n_list:
    #     m_notices = json.load(mock_n_list)
    # with open("news/test/fetchNoticeDetail.json", "r") as mock_n_body:
    #     m_single = json.load(mock_n_body)[3]
    with open("news/mocks/dt_response.json", "r") as mock_dt_r:
        m_dt = json.load(mock_dt_r)

    session = mock.Mock()
    # session.api.notice.fetchNotice.return_value = iceapi.api_return_t({}, 0, m_notices)
    # session.api.notice.fetchNoticeDetail.return_value = iceapi.api_return_t({}, 0, m_single)
    session.api.dailyTheater.fetchDailyTheater.return_value = iceapi.api_return_t(
        {}, 0, m_dt[3], m_dt[0]
    )
    return session


def end_session_2(context, ice):
    pass


def begin_session(context) -> iceapi.ICEBinder:
    return context.get_iceapi()


def end_session(context, ice: iceapi.ICEBinder):
    context.release_iceapi(ice)


def get_notice_body(ice, nid: int):
    ret = ice.api.notice.fetchNoticeDetail({"notice_id": nid})
    return ret.app_data["notice"].get("detail_text", {}).get("dot_under_text", "")


def pairwise(iterable):
    a = iter(iterable)
    return zip(a, a)


async def add_notice(ice, db, tag, notice):
    thumb = notice.get("banner_thumbnail", {}).get("v")
    title = notice.get("title", {}).get("dot_under_text", "")
    ts = datetime.utcfromtimestamp(notice["date"])
    nid = notice["notice_id"]
    cat = notice["category"]

    body_dm = get_notice_body(ice, nid)
    body_html, c_refs, _ = dm_parse.dm_to_html(body_dm.encode("utf8"), tag)

    logging.info("Adding notice: %s", nid)
    await db.insert_notice(tag, nid, title, ts, cat, thumb, body_dm, body_html, c_refs)


async def get_new_notices(ice, db, tag):
    since = await db.get_epoch(tag)
    ret = ice.api.notice.fetchNotice().app_data
    vis_set = set()
    seen = set()
    for _, the_list in pairwise(ret["notice_lists"]):
        for no in the_list["notices"]:
            vis_set.add(no["notice_id"])
            if datetime.utcfromtimestamp(no["date"]) <= since:
                continue
            if no["notice_id"] in seen:
                continue
            await add_notice(ice, db, tag, no)
            seen.add(no["notice_id"])

    await db.update_visibility(tag, list(vis_set))


async def get_daily_convo(ice, db, tag):
    since = await db.get_dt_epoch(tag)
    if datetime.now() < since:
        return

    ret = ice.api.dailyTheater.fetchDailyTheater().app_data
    next_info = ret.get("bootstrap_daily_theater_info")
    if not next_info or "next_opened_at" not in next_info:
        next_ts = datetime.utcfromtimestamp(0)
    else:
        try:
            next_ts = datetime.utcfromtimestamp(next_info["next_opened_at"])
        except (TypeError, ValueError):
            next_ts = datetime.utcfromtimestamp(0)

    ent = ret["daily_theater_detail"]
    title = ent["title"]["dot_under_text"]
    body_dm = ent["detail_text"]["dot_under_text"]
    ts = datetime.utcfromtimestamp(ent["date"])
    dtid = ent["daily_theater_id"]

    synth = dm_parse.dm_to_html_v2(
        body_dm.encode("utf8"), theatre_parse.TheatreScriptWalkState, tag
    )

    await db.add_dt(tag, dtid, ts, next_ts, title, body_dm, synth.get_json(), synth.char_refs)


async def main():
    logging.basicConfig(level=logging.INFO)
    tag = sys.argv[1]
    context = ctx.ASContext(tag, None, None)

    ice = begin_session(context)
    try:
        db = ingest.DatabaseConnection()
        await db.init_models()
        await get_new_notices(ice, db, tag)

        if tag not in DT_DISABLED_REGIONS:
            await get_daily_convo(ice, db, tag)
    finally:
        end_session(context, ice)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
