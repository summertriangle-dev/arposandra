import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import asyncpg

from captain.models.card_tracking import SUBTYPE_FES, SUBTYPE_PICK_UP
from captain.models.indexer.db_expert import PostgresDBExpert
from captain.models.mine_models import SetRecord, SetIndex
from libcard2 import dataclasses, string_mgr, master

from . import scripts
from .newsminer import AnySRecord, SEventRecord, SGachaMergeRecord

## Ordinal (gacha) based sets.

TSetMemory = List[Tuple[int, List[Tuple[List[int], SetRecord]]]]

SUBTYPE_SONG = 1001


class OrdinalSetWatcher(object):
    GROUP_NAMES = {1: "muse", 2: "aqours", 3: "nijigasaki"}
    CATEGORY_NAMES = {3: "fes", 2: "pickup", SUBTYPE_SONG: "singles"}
    # Maps gacha subtype (CATEGORY_NAMES) to set type (see card_tracking.py).
    #   SUBTYPE_SONG isn't a real subtype, it's just there for solo songs.
    SET_TYPES = {3: "ordinal_fes", 2: "ordinal_pickup", SUBTYPE_SONG: "song"}
    NEW_MEMBER_HOLDS = {
        # Initial Shio should belong to the Just Believe!!! set.
        # (which is ordinal 1 because LUMF is handled by the common-name code.)
        (210, SUBTYPE_SONG): 1
        # We expect Mia and Lanzhu to eventually have their own entries here.
    }

    def __init__(self):
        self.fes: TSetMemory = []
        self.pickup: TSetMemory = []
        self.song: TSetMemory = []
        self.max_ordinal = 0

    def make_slug(self, cat: int, grp: int, ord: int):
        # Something like "nijigasaki-fes-part1"
        return f"{self.GROUP_NAMES.get(grp)}-{self.CATEGORY_NAMES.get(cat)}-part{ord}"

    def getgroup(self, cat: int, grp: int):
        if cat == SUBTYPE_PICK_UP:
            src = self.pickup
        elif cat == SUBTYPE_FES:
            src = self.fes
        elif cat == SUBTYPE_SONG:
            src = self.song
        else:
            raise ValueError(f"{cat} is not a valid category.")

        for gid, lst in src:
            if gid == grp:
                return lst

        lst = []
        src.append((grp, lst))
        return lst

    def observe(self, card_id, ordinal, subtype, member_id, member_group):
        if ordinal <= self.max_ordinal:
            raise ValueError("observed ordinals must be monotonic")
        self.max_ordinal = ordinal

        sets = self.getgroup(subtype, member_group)
        for set_ord, (memory, setrecord) in enumerate(sets):
            if member_id not in memory and set_ord >= self.NEW_MEMBER_HOLDS.get(
                (member_id, subtype), 0
            ):
                memory.append(member_id)
                setrecord.members.append(card_id)
                break
        else:
            if subtype != SUBTYPE_SONG:
                tl_name = f"synthetic.cat{subtype}.g{member_group}.ord{len(sets)}"
            else:
                # This will break the systematic name generation, which is what we want. (card_page.py)
                tl_name = f"synthetic.singles.g{member_group}.ord{len(sets)}"

            new_set = SetRecord(
                self.make_slug(subtype, member_group, len(sets) + 1),
                tl_name,
                stype=self.SET_TYPES.get(subtype),
            )
            new_set.members.append(card_id)
            sets.append(([member_id], new_set))

    def generate_sets(self) -> Iterable[SetRecord]:
        for gid, lst in self.fes:
            for _, collection in lst:
                yield collection

        for gid, lst in self.pickup:
            for _, collection in lst:
                yield collection

        for gid, lst in self.song:
            for _, collection in lst:
                yield collection


# TODO: Should checkpoint this so we aren't reading the entire index every time.
async def update_ordinal_sets(conn: asyncpg.Connection, set_expert: PostgresDBExpert):
    watcher = OrdinalSetWatcher()
    rset = await conn.fetch(
        """
        SELECT DISTINCT ON (ordinal) card_index_v1.id, ordinal, member_group, member, subtype
        FROM history_v5__card_ids 
        INNER JOIN history_v5 USING (id, serverid) 
        INNER JOIN card_index_v1 ON (card_id = card_index_v1.id) 
        WHERE (subtype = 2 OR subtype = 3) AND rarity = 30 AND serverid = 'jp' AND history_v5__card_ids.what > 1
        ORDER BY ordinal, sort_date
        """
    )

    for cid, ordinal, member_group, member, subtype in rset:
        watcher.observe(cid, ordinal, subtype, member, member_group)

    async with conn.transaction():
        for s in watcher.generate_sets():
            await set_expert.add_object(conn, s)


## Song sets.

# This *may* not always return the same representative for each common name,
# which sucks, but it is handled up in update_card_index. Keep that in mind if you plan to
# reuse the output of this function somewhere else.
def find_potential_set_names(from_lang: string_mgr.DictionaryAccess) -> List[Tuple[str, str, bool]]:
    db = from_lang.get_dictionary_handle("k")
    script = """
        -- Equivalent to "id LIKE 'card_name_awaken_%'. But using the comparisons
        -- lets sqlite use the index.

        SELECT "k." || m_dictionary.id, m_dictionary.message, L.message NOT NULL AS is_song FROM m_dictionary 
		LEFT JOIN m_dictionary as L ON (L.id > "song_name_" AND L.id < "song_name_z" AND L.message = m_dictionary.message)
        WHERE (m_dictionary.id > "card_name_awaken_" AND m_dictionary.id < "card_name_awaken_:"  
                AND length(m_dictionary.id) = length("card_name_awaken_400092001"))
        GROUP BY m_dictionary.message HAVING COUNT(m_dictionary.message) > 1 ORDER BY COUNT(m_dictionary.message) DESC
    """
    return db.execute(script).fetchall()


def find_solo_song_card_names(from_lang: string_mgr.DictionaryAccess) -> List[str]:
    db = from_lang.get_dictionary_handle("k")
    script = """
        SELECT "k." || m_dictionary.id FROM m_dictionary 
        INNER JOIN m_dictionary as L ON (L.id > "song_name_" AND L.id < "song_name_z" AND L.message = m_dictionary.message)
        WHERE (m_dictionary.id > "card_name_awaken_" AND m_dictionary.id < "card_name_awaken_:"  
                AND length(m_dictionary.id) = length("card_name_awaken_400092001"))
        GROUP BY m_dictionary.message HAVING COUNT(m_dictionary.message) = 1
    """
    return [name for name, in db.execute(script).fetchall()]


async def generate_solo_sets(
    conn: asyncpg.Connection,
    db: master.MasterData,
    using_dict: string_mgr.DictionaryAccess,
):
    watcher = OrdinalSetWatcher()

    script = """
        SELECT m_card.id, school_idol_no, member_m_id, m_member.member_group, m_card_appearance.card_name
        FROM m_card 
            INNER JOIN m_member ON (member_m_id = m_member.id)
            INNER JOIN m_card_appearance ON (m_card.id = m_card_appearance.card_m_id)
        ORDER BY school_idol_no
    """
    capture_set = find_solo_song_card_names(using_dict)
    for cid, ordinal, mid, mgrp, name in db.connection.execute(script):
        if name not in capture_set:
            continue

        watcher.observe(cid, ordinal, SUBTYPE_SONG, mid, mgrp)

    set_expert = PostgresDBExpert(SetIndex)
    async with conn.transaction():
        for s in watcher.generate_sets():
            # Ignore sets with a single card, since they may be common-name sets in a later release.
            if len(s.members) > 1:
                await set_expert.add_object(conn, s)


## Event sets


def is_event_srecord(rec: AnySRecord):
    return isinstance(rec, SEventRecord) or rec.maybe_type == SGachaMergeRecord.T_EVENT_TIE


def get_card_list(rec: AnySRecord):
    return (
        rec.feature_card_ids if isinstance(rec, SEventRecord) else set(rec.feature_card_ids.keys())
    )


def filter_sets(
    sets: List[SetRecord], events: List[AnySRecord], is_authoritative: bool
):
    cache = {
        x.record_id: x.feature_card_ids
        if isinstance(x, SEventRecord)
        else set(x.feature_card_ids.keys())
        for x in events
    }
    marks = []

    for s in sets:
        if len(s.members) < 2:
            continue

        for rid, cset in cache.items():
            # Avoid being overzealous and consuming sr costume sets.
            if cset.issuperset(s.members) and len(cset.intersection(s.members)) > 1:
                s.members = list(cset)
                s.stype = "event"
                marks.append(rid)

        yield s

    if is_authoritative:
        for evt in events:
            if evt.record_id in marks or not is_event_srecord(evt):
                continue

            logging.debug("Creating a set for event release from %s.", evt.common_title)
            yield SetRecord(evt.common_title, evt.common_title, "event", list(get_card_list(evt)))
