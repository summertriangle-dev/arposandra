from datetime import datetime, timezone
from collections import defaultdict


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

    async def get_event_info(self, server_id, event_id):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetchrow(
                """
                SELECT event_id, banner, event_type, start_t, end_t, result_t FROM event_v2
                WHERE serverid=$1 AND event_id=$2
                """,
                server_id,
                event_id,
            )

    async def get_current_event(self, server_id, timestamp):
        async with self.coordinator.pool.acquire() as c:
            return await c.fetchrow(
                """
                SELECT event_id, banner, event_type, start_t, end_t, result_t FROM event_v2
                WHERE serverid=$1 AND start_t <= $2 ORDER BY end_t DESC
                """,
                server_id,
                timestamp,
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
                SELECT observation FROM border_fixed_data_v3
                WHERE serverid=$1 AND event_id=$2
                ORDER BY observation DESC LIMIT 1
            )

            SELECT observation, tier_type AS dataset,
                points_t1, points_t2, points_t3, points_t4, points_t5,
                points_t6, points_t7, points_t8, points_t9, points_t10
            FROM border_fixed_data_v3 WHERE serverid=$1 AND event_id=$2
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
                points_t6, points_t7, points_t8, points_t9, points_t10
            FROM border_fixed_data_v3 WHERE serverid=$1 AND event_id=$2 AND observation > $3
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
                recs = await self._fetch_new_t10_recs(c, server_id, event_id)

            for record in recs:
                for x in range(1, 11):
                    datasets[f"{record['dataset']}.t{x}"].append(
                        (self.to_utc_timestamp(record["observation"]), record[f"points_t{x}"])
                    )

        return datasets
