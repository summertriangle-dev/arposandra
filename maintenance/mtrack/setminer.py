from typing import List, Tuple, Dict, Iterable
from dataclasses import dataclass
import asyncpg

from libcard2 import string_mgr, dataclasses

from captain.models.indexer.db_expert import PostgresDBExpert
from captain.models.card_tracking import SUBTYPE_FES, SUBTYPE_PICK_UP
from captain.models.mine_models import SetRecord

from . import scripts

TSetMemory = List[Tuple[int, List[Tuple[List[int], SetRecord]]]]


class OrdinalSetWatcher(object):
    def __init__(self):
        self.fes: TSetMemory = []
        self.pickup: TSetMemory = []
        self.max_ordinal = 0

    def getgroup(self, cat: int, grp: int):
        if cat == SUBTYPE_PICK_UP:
            src = self.pickup
        else:
            src = self.fes

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
        for memory, setrecord in sets:
            if member_id not in memory:
                memory.append(member_id)
                setrecord.members.append(card_id)
                break
        else:
            new_set = SetRecord(
                f"synthetic set",
                f"synthetic.cat{subtype}.g{member_group}.ord{len(sets)}",
                stype="ordinal_fes" if subtype == 3 else "ordinal_pickup",
            )
            new_set.members.append(card_id)
            sets.append(([member_id], new_set))

    def generate_sets(self) -> Iterable[SetRecord]:
        for gid, lst in self.fes:
            for _, collection in lst:
                print(collection)
                yield collection

        for gid, lst in self.pickup:
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
	    INNER JOIN card_index_v1 ON (card_ids = card_index_v1.id) 
	    WHERE (subtype = 2 OR subtype = 3) AND rarity = 30 AND serverid = 'jp' AND what = 1
	    ORDER BY ordinal, start_time
        """
    )

    for cid, ordinal, member_group, member, subtype in rset:
        watcher.observe(cid, ordinal, subtype, member, member_group)

    async with conn.transaction():
        for s in watcher.generate_sets():
            await set_expert.add_object(conn, s)
        await conn.execute(scripts.update_set_per_server_release_dates_synthetic())


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
