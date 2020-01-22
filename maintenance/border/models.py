import os
from datetime import datetime
import json
from collections import namedtuple

import asyncpg


event_status_t = namedtuple(
    "event_status_t", ("start_time", "end_time", "results_time", "last_collect_time", "have_final")
)


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def init_models(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                """
                DO $$ BEGIN
                    CREATE TYPE tier_type_t AS ENUM ('points', 'voltage');
                EXCEPTION
                    WHEN duplicate_object THEN null;
                END $$;
                
                CREATE TABLE IF NOT EXISTS event_v2 (
                    serverid varchar(8),
                    event_id int,
                    event_title text,
                    banner text,
                    event_type text,
                    start_t timestamp,
                    end_t timestamp,
                    result_t timestamp,

                    UNIQUE(serverid, event_id)
                );
                CREATE TABLE IF NOT EXISTS event_story_v2 (
                    serverid varchar(8),
                    event_id int,
                    chapter int,
                    req_points int,
                    banner text,
                    title text,
                    script_path text,

                    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS border_fixed_data_v3 (
                    serverid varchar(8),
                    event_id int,
                    observation timestamp,
                    is_last boolean,

                    tier_type tier_type_t,
                    points_t1 int, userid_t1 int,
                    points_t2 int, userid_t2 int,
                    points_t3 int, userid_t3 int,
                    points_t4 int, userid_t4 int,
                    points_t5 int, userid_t5 int,
                    points_t6 int, userid_t6 int,
                    points_t7 int, userid_t7 int,
                    points_t8 int, userid_t8 int,
                    points_t9 int, userid_t9 int,
                    points_t10 int, userid_t10 int,

                    UNIQUE (serverid, event_id, tier_type, observation),
                    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS border_data_v3 (
                    serverid varchar(8),
                    event_id int,
                    observation timestamp,
                    is_last boolean,

                    tier_type tier_type_t,
                    points int,
                    tier_from int,
                    tier_to int,

                    UNIQUE(serverid, event_id, tier_type, tier_to, observation),
                    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS border_t100_v1 (
                    serverid varchar(8),
                    event_id int,
                    tier_type tier_type_t,

                    rank int,
                    points int,
                    user_id int,
                    user_name text,
                    user_level int,
                    center_card int,
                    center_level int,
                    awakened boolean,
                    full_tree boolean,
                    wield_title int,

                    UNIQUE(serverid, event_id, tier_type, rank),
                    FOREIGN KEY (serverid, event_id) REFERENCES event_v2(serverid, event_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                """
            )

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
