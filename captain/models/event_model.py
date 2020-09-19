from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List

from .card_tracking import HistoryRecord


@dataclass
class EventID(object):
    server_id: str
    id: int
    type: int

    title: str
    thumbnail: str
    feature_card_ids: List[int]

    start_t: datetime
    end_t: datetime
    result_t: datetime


class EventTrackingDatabase(object):
    SERVER_IDS = ["jp", "en"]

    def __init__(self, coordinator):
        self.coordinator = coordinator

    @staticmethod
    def to_utc_timestamp(naive):
        return naive.replace(tzinfo=timezone.utc).timestamp()

    def validate_server_id(self, server_id):
        if server_id not in self.SERVER_IDS:
            return self.SERVER_IDS[0]
        return server_id

    async def get_event_info(self, server_id, event_id) -> EventID:
        async with self.coordinator.pool.acquire() as c:
            the_row = await c.fetchrow(
                """
                SELECT event_id, event_type, start_t, end_t, result_t,
                    title, thumbnail, ARRAY(SELECT card_id FROM history_v5__card_ids 
                    WHERE history_v5__card_ids.id = history_v5.id
                    AND history_v5__card_ids.serverid = $1
                    AND history_v5__card_ids.what = 1) AS card_ids
                FROM event_v2
                LEFT JOIN history_v5__dates ON (event_v2.serverid = history_v5__dates.serverid
                    AND event_v2.event_id = history_v5__dates.value 
                    AND history_v5__dates.type = 7)
                LEFT JOIN history_v5 ON (history_v5__dates.serverid = history_v5.serverid 
                    AND history_v5__dates.id = history_v5.id)
                WHERE event_v2.serverid=$1 AND event_id=$2
                """,
                server_id,
                event_id,
            )

        return EventID(
            server_id,
            the_row["event_id"],
            the_row["event_type"],
            the_row["title"],
            the_row["thumbnail"],
            the_row["card_ids"],
            the_row["start_t"],
            the_row["end_t"],
            the_row["result_t"],
        )

    async def get_current_event(self, server_id, timestamp) -> EventID:
        async with self.coordinator.pool.acquire() as c:
            the_row = await c.fetchrow(
                """
                SELECT event_id, event_type, start_t, end_t, result_t,
                    title, thumbnail, ARRAY(SELECT card_id FROM history_v5__card_ids 
                    WHERE history_v5__card_ids.id = history_v5.id
                    AND history_v5__card_ids.serverid = $1
                    AND history_v5__card_ids.what = 1) AS card_ids
                FROM event_v2
                LEFT JOIN history_v5__dates ON (event_v2.serverid = history_v5__dates.serverid
                    AND event_v2.event_id = history_v5__dates.value 
                    AND history_v5__dates.type = 7)
                LEFT JOIN history_v5 ON (history_v5__dates.serverid = history_v5.serverid 
                    AND history_v5__dates.id = history_v5.id)
                WHERE event_v2.serverid=$1 AND start_t <= $2 ORDER BY end_t DESC
                """,
                server_id,
                timestamp,
            )

        return EventID(
            server_id,
            the_row["event_id"],
            the_row["event_type"],
            the_row["title"],
            the_row["thumbnail"],
            the_row["card_ids"],
            the_row["start_t"],
            the_row["end_t"],
            the_row["result_t"],
        )

    async def get_stories(self, server_id, event_id):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetch(
                """
                SELECT chapter, req_points, banner, title, script_path FROM event_story_v2
                WHERE serverid=$1 AND event_id=$2 ORDER BY chapter
                """,
                server_id,
                event_id,
            )

    async def _fetch_new_tier_recs(self, con, server_id, event_id, tscale):
        return await con.fetch(
            """
            WITH closest AS (
                SELECT observation FROM border_data_v3
                WHERE serverid=$1 AND event_id=$2
                ORDER BY observation DESC LIMIT 1
            )

            SELECT observation, CONCAT_WS('.', tier_type, tier_to) AS dataset, points
            FROM border_data_v3 WHERE serverid=$1 AND event_id=$2
            AND observation > (SELECT observation FROM closest) - make_interval(hours => $3)
            ORDER BY observation
            """,
            server_id,
            event_id,
            tscale,
        )

    async def _fetch_tiers_with_afterts(self, con, server_id, event_id, ts):
        return await con.fetch(
            """
            SELECT observation, CONCAT_WS('.', tier_type, tier_to) AS dataset,
                points
            FROM border_data_v3 WHERE serverid=$1 AND event_id=$2 AND observation > $3
            ORDER BY observation
            """,
            server_id,
            event_id,
            ts,
        )

    async def get_tier_records(self, server_id, event_id, after_dt):
        datasets = defaultdict(lambda: [])
        async with self.coordinator.pool.acquire() as c:
            if isinstance(after_dt, datetime):
                recs = await self._fetch_tiers_with_afterts(c, server_id, event_id, after_dt)
            else:
                recs = await self._fetch_new_tier_recs(c, server_id, event_id, after_dt)

            for record in recs:
                datasets[record["dataset"]].append(
                    (self.to_utc_timestamp(record["observation"]), record["points"])
                )

        return datasets

    async def _fetch_new_t10_recs(self, con, server_id, event_id, tscale):
        return await con.fetch(
            """
            WITH closest AS (
                SELECT observation FROM border_fixed_data_v4
                WHERE serverid=$1 AND event_id=$2
                ORDER BY observation DESC LIMIT 1
            )

            SELECT observation, tier_type AS dataset,
                points_t1, points_t2, points_t3, points_t4, points_t5,
                points_t6, points_t7, points_t8, points_t9, points_t10,
                points_t11, points_t12, points_t13, points_t14, points_t15,
                points_t16, points_t17, points_t18, points_t19, points_t20,
                who_t1, who_t2, who_t3, who_t4, who_t5,
                who_t6, who_t7, who_t8, who_t9, who_t10,
                who_t11, who_t12, who_t13, who_t14, who_t15,
                who_t16, who_t17, who_t18, who_t19, who_t20
            FROM border_fixed_data_v4 WHERE serverid=$1 AND event_id=$2
            AND observation > (SELECT observation FROM closest) - make_interval(hours => $3)
            ORDER BY observation
            """,
            server_id,
            event_id,
            tscale,
        )

    async def _fetch_t10_afterts(self, con, server_id, event_id, ts):
        return await con.fetch(
            """
            SELECT observation, tier_type AS dataset,
                points_t1, points_t2, points_t3, points_t4, points_t5,
                points_t6, points_t7, points_t8, points_t9, points_t10,
                points_t11, points_t12, points_t13, points_t14, points_t15,
                points_t16, points_t17, points_t18, points_t19, points_t20,
                who_t1, who_t2, who_t3, who_t4, who_t5,
                who_t6, who_t7, who_t8, who_t9, who_t10,
                who_t11, who_t12, who_t13, who_t14, who_t15,
                who_t16, who_t17, who_t18, who_t19, who_t20
            FROM border_fixed_data_v4 WHERE serverid=$1 AND event_id=$2 AND observation > $3
            ORDER BY observation
            """,
            server_id,
            event_id,
            ts,
        )

    async def get_t10_records(self, server_id, event_id, after_dt):
        datasets = defaultdict(lambda: [])
        async with self.coordinator.pool.acquire() as c:
            if isinstance(after_dt, datetime):
                recs = await self._fetch_t10_afterts(c, server_id, event_id, after_dt)
            else:
                recs = await self._fetch_new_t10_recs(c, server_id, event_id, after_dt)

            for record in recs:
                for x in range(1, 21):
                    datasets[f"{record['dataset']}.{x}"].append(
                        (
                            self.to_utc_timestamp(record["observation"]),
                            record[f"points_t{x}"],
                            record[f"who_t{x}"],
                        )
                    )

        return datasets
