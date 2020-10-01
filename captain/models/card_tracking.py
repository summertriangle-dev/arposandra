import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Any, Dict, Union

from libcard2.dataclasses import Card

Timespan = Tuple[datetime, timedelta]

TYPE_GACHA = 1
TYPE_EVENT = 2

SUBTYPE_EVENT_TIE = 1
SUBTYPE_PICK_UP = 2
SUBTYPE_FES = 3
SUBTYPE_ELSE = 4
SUBTYPE_IGNORE = -1

MAP_WHAT_TO_ID = {1: "event", 2: "gacha", 3: "gacha_part2"}


@dataclass
class HistoryRecord(object):
    T_DATE_EVENT_START = 1
    T_DATE_GACHA_START = 2
    T_DATE_GACHA2_START = 3
    T_DATE_EVENT_END = 4
    T_DATE_GACHA_END = 5
    T_DATE_GACHA2_END = 6
    T_DATE_INGAME_EVENT_ID = 7

    record_id: int
    server_id: int
    common_title: str
    feature_card_ids: Dict[str, List[int]]
    major_type: int
    sub_type: int
    thumbnail: str
    dates: Dict[int, Union[int, datetime]]

    def event_dates(self):
        return (self.dates.get(self.T_DATE_EVENT_START), self.dates.get(self.T_DATE_EVENT_END))

    def gacha_dates(self):
        return (self.dates.get(self.T_DATE_GACHA_START), self.dates.get(self.T_DATE_GACHA_END))

    def gacha_part2_dates(self):
        return (self.dates.get(self.T_DATE_GACHA2_START), self.dates.get(self.T_DATE_GACHA2_END))

    def nom_date(self):
        return self.dates.get(self.T_DATE_GACHA_START) or self.dates.get(self.T_DATE_EVENT_START)

    def ig_event_id(self):
        return self.dates.get(self.T_DATE_INGAME_EVENT_ID)

    def all_card_ids(self):
        for (k, v) in sorted(self.feature_card_ids.items()):
            yield from v

    @staticmethod
    def card_list(l: List[Tuple[int, int]]) -> Dict[str, List[int]]:
        gs: Dict[str, List[int]] = {}
        for cid, what in l:
            ins = gs.get(MAP_WHAT_TO_ID[what])
            if ins is None:
                gs[MAP_WHAT_TO_ID[what]] = [cid]
            else:
                ins.append(cid)

        return gs

    @classmethod
    def unpack_dates(cls, l: List[Tuple[int, datetime, int]]) -> Dict[int, Union[int, datetime]]:
        gs: Dict[int, Union[int, datetime]] = {}
        for vid, date, val in l:
            if vid >= cls.T_DATE_INGAME_EVENT_ID:
                gs[vid] = val
            else:
                gs[vid] = date

        return gs


@dataclass
class CardSetRecord(object):
    T_DEFAULT = 1
    T_EVENT = 2
    T_SONG = 3
    T_FES = 4
    T_PICKUP = 5

    @dataclass
    class ID(object):
        id: int
        source: int
        release: datetime
        card: Card = field(init=False)

    name: str
    representative: str
    set_type: int
    card_refs: List[ID]
    shioriko_exists: bool

    def is_systematic(self):
        return self.set_type in [4, 5]

    def max_date(self):
        return max(x.release for x in self.card_refs if x.release)

    @staticmethod
    def unpack_rdates(lrecs):
        return [CardSetRecord.ID(*x) for x in lrecs]


class CardTrackingDatabase(object):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def get_history_entry_count(self, for_server: str, subtype: int = None) -> int:
        args: List[Any] = [for_server]
        query = [
            """SELECT COUNT(0) AS count FROM history_v5
                WHERE serverid = $1"""
        ]
        if subtype is not None:
            query.append("AND subtype = $2")
            args.append(subtype)

        async with self.coordinator.pool.acquire() as conn:
            return (await conn.fetchrow("\n".join(query), *args))["count"]

    async def get_history_entries(
        self, for_server: str, subtype: int = None, page: int = 0, n_entries: int = 20,
    ) -> List[HistoryRecord]:
        offset = page * n_entries

        act = 2
        args: List[Any] = [for_server]
        footer = f"\nORDER BY sort_date DESC LIMIT {n_entries + 1} OFFSET {offset}"
        query = """
            SELECT id, serverid, title, what, subtype, thumbnail,
            ARRAY(SELECT (card_id, what) FROM history_v5__card_ids 
	                WHERE history_v5__card_ids.id = history_v5.id
                    AND history_v5__card_ids.serverid = $1) AS card_ids,
            ARRAY(SELECT (type, date, value) FROM history_v5__dates
	                WHERE history_v5__dates.id = history_v5.id
                    AND history_v5__dates.serverid = $1) AS dates
			FROM history_v5
			WHERE serverid = $1
        """

        if subtype is not None:
            query += f"\nAND subtype = ${act}"
            args.append(subtype)
            act += 1

        query += footer

        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(query, *args)

        return [
            HistoryRecord(
                i["id"],
                i["serverid"],
                i["title"],
                HistoryRecord.card_list(i["card_ids"]),
                i["what"],
                i["subtype"],
                i["thumbnail"],
                HistoryRecord.unpack_dates(i["dates"]),
            )
            for i in items
        ]

    async def get_card_set_count(self, category: int = None, tag: str = None) -> int:
        if tag is None:
            tag = "jp"

        args: List[Any] = [tag]
        query = [
            """
            SELECT COUNT(0) AS count FROM card_p_set_index_v1__sort_dates
            INNER JOIN card_p_set_index_v1 USING (representative)
            WHERE server_id = $1
        """
        ]
        if category is not None:
            query.append("AND set_type = $2")
            args.append(category)

        async with self.coordinator.pool.acquire() as conn:
            return (await conn.fetchrow("\n".join(query), *args))["count"]

    async def get_card_sets(
        self, category: int = None, page: int = None, n_entries: int = 20, tag: str = None,
    ) -> List[CardSetRecord]:
        if tag is None:
            tag = "jp"

        offset = 0
        if page:
            offset = page * n_entries

        query = f"""
            WITH wanted_entries AS (
                SELECT card_p_set_index_v1.id, card_p_set_index_v1.representative, set_type, shioriko_exists
                FROM card_p_set_index_v1
                INNER JOIN card_p_set_index_v1__sort_dates USING (representative)
                WHERE server_id = $1
                {"AND set_type = $2" if category is not None else ""}
			    ORDER BY date DESC LIMIT {n_entries} OFFSET {offset}
            )
			
			SELECT *, ARRAY(
                SELECT (card_ids, source, date) FROM card_p_set_index_v1__card_ids 
                INNER JOIN card_index_v1 ON (card_index_v1.id = card_p_set_index_v1__card_ids.card_ids)
                LEFT JOIN card_index_v1__release_dates ON (
                    card_index_v1.id = card_index_v1__release_dates.id 
                    AND server_id = $1
                )
                WHERE card_p_set_index_v1__card_ids.representative = wanted_entries.representative 
            ) AS cards
			FROM wanted_entries
        """

        args: List[Any] = [tag]
        if category is not None:
            args.append(category)

        async with self.coordinator.pool.acquire() as conn:
            set_ids = await conn.fetch(query, *args)
            return [
                CardSetRecord(
                    r["id"],
                    r["representative"],
                    r["set_type"],
                    CardSetRecord.unpack_rdates(r["cards"]),
                    bool(r["shioriko_exists"]),
                )
                for r in set_ids
            ]

    async def get_single_card_set(self, name: str) -> Optional[CardSetRecord]:
        query = f"""
            SELECT card_p_set_index_v1.id, card_p_set_index_v1.representative, set_type, shioriko_exists,
            ARRAY(
                SELECT (card_ids, source, date) FROM card_p_set_index_v1__card_ids 
                INNER JOIN card_index_v1 ON (card_index_v1.id = card_p_set_index_v1__card_ids.card_ids)
                LEFT JOIN card_index_v1__release_dates ON (
                    card_index_v1.id = card_index_v1__release_dates.id 
                    AND server_id = $1
                )
                WHERE card_p_set_index_v1__card_ids.representative = card_p_set_index_v1.representative 
            ) AS cards
            FROM card_p_set_index_v1__sort_dates
            INNER JOIN card_p_set_index_v1 USING (representative)
            WHERE server_id = $1 AND id = $2 LIMIT 1
        """

        async with self.coordinator.pool.acquire() as conn:
            the_set = await conn.fetchrow(query, "jp", name)
            if not the_set:
                return None

            return CardSetRecord(
                the_set["id"],
                the_set["representative"],
                the_set["set_type"],
                CardSetRecord.unpack_rdates(the_set["cards"]),
                bool(the_set["shioriko_exists"]),
            )

