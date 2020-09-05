import json
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple, Any

Timespan = Tuple[datetime, timedelta]

TYPE_GACHA = 1
TYPE_EVENT = 2

SUBTYPE_EVENT_TIE = 1
SUBTYPE_PICK_UP = 2
SUBTYPE_FES = 3
SUBTYPE_ELSE = 4
SUBTYPE_IGNORE = -1


@dataclass
class UnifiedSRecord(object):
    record_id: int
    server_id: int
    common_title: str
    feature_card_ids: List[int]
    major_type: int
    sub_type: int
    thumbnail: str
    start_time: datetime
    end_time: datetime


@dataclass
class CardSetRecord(object):
    T_DEFAULT = 1
    T_EVENT = 2
    T_SONG = 3
    T_FES = 4
    T_PICKUP = 5

    name: str
    representative: str
    set_type: int
    min_date: datetime
    max_date: datetime
    card_refs: List[int]
    original_release: datetime


class CardTrackingDatabase(object):
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def get_history_entries(
        self,
        for_server: str,
        category: int = None,
        subtype: int = None,
        before_date: datetime = None,
        n_entries: int = 20,
    ) -> List[UnifiedSRecord]:
        act = 2
        args: List[Any] = [for_server]
        footer = f"\nORDER BY start_time DESC LIMIT {n_entries}"
        query = """
            SELECT id, serverid, title, 
            ARRAY(SELECT card_ids FROM history_v5__card_ids 
	            WHERE history_v5__card_ids.serverid = history_v5.serverid 
                AND history_v5__card_ids.id=history_v5.id) AS card_ids,
            what, subtype, thumbnail, start_time, end_time
            FROM history_v5 WHERE serverid = $1
        """

        if category is not None:
            query += f"\nAND what = ${act}"
            args.append(category)
            act += 1
        elif subtype is not None:
            query += f"\nAND subtype = ${act}"
            args.append(subtype)
            act += 1
        elif before_date is not None:
            query += f"\nAND start_time < ${act}"
            args.append(before_date)
            act += 1

        query += footer

        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(query, *args)

        return [
            UnifiedSRecord(
                i["id"],
                i["serverid"],
                i["title"],
                i["card_ids"],
                i["what"],
                i["subtype"],
                i["thumbnail"],
                i["start_time"],
                i["end_time"],
            )
            for i in items
        ]

    def collect_card_ids(self, rows):
        buckets = defaultdict(lambda: [])
        for row in rows:
            buckets[row["representative"]].append(row["card_ids"])

        return buckets

    async def get_card_sets(
        self, category: int = None, page: int = None, n_entries: int = 20, tag: str = None,
    ) -> Tuple[List[CardSetRecord], bool]:
        if tag is None:
            tag = "jp"

        offset = 0
        if page:
            offset = page * n_entries

        query = [
            f"""
            SELECT id, card_p_set_index_v1.representative, set_type,
            ARRAY(SELECT card_ids FROM card_p_set_index_v1__card_ids 
	            WHERE card_p_set_index_v1__card_ids.representative = card_p_set_index_v1.representative 
            ) AS card_ids, card_p_set_index_v1__release_dates.min_date, 
            card_p_set_index_v1__release_dates.max_date, 
            orig_rls.min_date AS orig_rlsd
            FROM card_p_set_index_v1
            LEFT JOIN card_p_set_index_v1__release_dates ON 
                (card_p_set_index_v1__release_dates.representative = card_p_set_index_v1.representative 
                 AND card_p_set_index_v1__release_dates.server_id = $1)
            LEFT JOIN card_p_set_index_v1__release_dates AS orig_rls ON 
                (orig_rls.representative = card_p_set_index_v1.representative 
                 AND orig_rls.server_id = 'jp')
            WHERE card_p_set_index_v1__release_dates.max_date IS NOT NULL
            """
        ]
        args: List[Any] = [tag]
        if category is not None:
            query.append(f"AND set_type = ${len(args) + 1}")
            args.append(category)

        query.append(
            f"ORDER BY card_p_set_index_v1__release_dates.max_date DESC LIMIT {n_entries + 1} OFFSET {offset}"
        )

        async with self.coordinator.pool.acquire() as conn:
            set_ids = await conn.fetch("\n".join(query), *args)
            if len(set_ids) > n_entries:
                have_more = True
            else:
                have_more = False

            return (
                [
                    CardSetRecord(
                        r["id"],
                        r["representative"],
                        r["set_type"],
                        r["min_date"],
                        r["max_date"],
                        r["card_ids"],
                        r["orig_rlsd"],
                    )
                    for r in set_ids[:n_entries]
                ],
                have_more,
            )
