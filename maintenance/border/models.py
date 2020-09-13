import os
from datetime import datetime
import json
from collections import namedtuple

import asyncpg
import pkg_resources

from captain.models.indexer import db_expert
from captain.models import mine_models

event_status_t = namedtuple(
    "event_status_t", ("start_time", "end_time", "results_time", "last_collect_time", "have_final")
)


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def init_models(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)
        init_schema = pkg_resources.resource_string("captain", "init_schema.sql").decode("utf8")
        hist_expert = db_expert.PostgresDBExpert(mine_models.HistoryIndex)
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(init_schema)
            await hist_expert.create_tables(c)

    async def have_event_info(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow(
                """SELECT COUNT(0) FROM event_v2 WHERE serverid=$1 AND event_id=$2""",
                region,
                event_id,
            )
            if row[0]:
                return True
            return False

    async def have_final_tiers(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow(
                """SELECT is_last FROM border_data_v3 WHERE serverid=$1 AND event_id=$2 AND is_last=TRUE""",
                region,
                event_id,
            )
            if row:
                return True
            return False

    async def get_event_timing(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow(
                """SELECT end_t, result_t FROM event_v2 WHERE serverid=$1 AND event_id=$2""",
                region,
                event_id,
            )

            if not row:
                return None, None
            return row[0], row[1]

    async def get_event_status(self, region, event_id):
        async with self.pool.acquire() as c:
            desc = await c.fetchrow(
                """
                SELECT start_t, end_t, result_t FROM event_v2 WHERE serverid=$1 AND event_id=$2
                LIMIT 1
                """,
                region,
                event_id,
            )

            if not desc:
                return None

            obs, fin = None, False
            last_collect = await c.fetchrow(
                """
                SELECT observation, is_last FROM border_data_v3 WHERE serverid=$1 AND event_id=$2 
                ORDER BY observation DESC LIMIT 1
                """,
                region,
                event_id,
            )

            if last_collect:
                obs = last_collect["observation"]
                fin = last_collect["is_last"]

            return event_status_t(desc["start_t"], desc["end_t"], desc["result_t"], obs, fin)

    async def add_event(
        self, region, event_id, event_title, banner, event_type, start, end, results, stories
    ):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                """
                INSERT INTO event_v2 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                region,
                event_id,
                event_title,
                banner,
                event_type,
                datetime.utcfromtimestamp(start),
                datetime.utcfromtimestamp(end),
                datetime.utcfromtimestamp(results),
            )

            await c.executemany(
                """
                INSERT INTO event_story_v2 VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                stories,
            )
        await self.update_mtrack_event_links()

    async def add_tiers(self, region, event_id, time, is_last, rows, singular):
        time = time.replace(second=0, microsecond=0)

        async with self.pool.acquire() as c, c.transaction():
            await c.executemany(
                """
                INSERT INTO border_fixed_data_v3 VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15,
                    $16, $17, $18, $19, $20, $21, $22, $23, $24, $25)
                ON CONFLICT (serverid, event_id, tier_type, observation) DO NOTHING
                """,
                ((region, event_id, time, is_last, *r) for r in singular),
            )
            await c.executemany(
                """
                INSERT INTO border_data_v3 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (serverid, event_id, tier_type, tier_to, observation) DO NOTHING
                """,
                ((region, event_id, time, is_last, *r) for r in rows),
            )

    async def add_t100(self, region, event_id, type_, rows):
        async with self.pool.acquire() as c, c.transaction():
            await c.executemany(
                """
                INSERT INTO border_t100_v1 VALUES
                ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                ON CONFLICT (serverid, event_id, tier_type, rank) DO NOTHING 
                """,
                ((region, event_id, type_, *r) for r in rows),
            )

    async def clear_norm_tiers(self, region, event_id):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute("DELETE FROM border_data_v3")

    async def update_mtrack_event_links(self):
        query = """
            WITH event_match AS (
                SELECT event_v2.serverid AS sid, event_id, history_v5__dates.id AS hid FROM history_v5__dates 
                INNER JOIN event_v2 ON (history_v5__dates.serverid=event_v2.serverid 
                    AND EXTRACT(epoch FROM history_v5__dates.date - event_v2.start_t) <= 0)
                WHERE type = 1
            )

            INSERT INTO history_v5__dates (
                (SELECT hid, sid, NULL, event_id FROM event_match)
            ) ON CONFLICT DO NOTHING;
        """
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(query)
