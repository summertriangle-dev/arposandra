import os
from datetime import datetime
import json

import asyncpg


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def init_models(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS event_v1 (
                    serverid varchar(8),
                    event_id int,
                    event_title text,
                    banner text,
                    event_type text,
                    start_t timestamp,
                    end_t timestamp,
                    result_t timestamp
                );
                CREATE TABLE IF NOT EXISTS event_story_v1 (
                    serverid varchar(8),
                    event_id int,
                    chapter int,
                    req_points int,
                    banner text,
                    title text,
                    script_path text
                );
                CREATE TABLE IF NOT EXISTS border_data_v1 (
                    serverid varchar(8),
                    event_id int,
                    observation timestamp,
                    is_last boolean,

                    tier_type varchar(8),
                    points int,
                    tier_from int,
                    tier_to int,
                    ordering int
                );
                """
            )
    
    async def have_event_info(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow("""SELECT COUNT(0) FROM event_v1 WHERE serverid=$1 AND event_id=$2""",
                region, event_id)
            if row[0]:
                return True
            return False
    
    async def have_final_tiers(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow("""SELECT is_last FROM border_data_v1 WHERE serverid=$1 AND event_id=$2 AND is_last=TRUE""",
                region, event_id)
            if row:
                return True
            return False
    
    async def get_event_timing(self, region, event_id):
        async with self.pool.acquire() as c:
            row = await c.fetchrow("""SELECT end_t, result_t FROM event_v1 WHERE serverid=$1 AND event_id=$2""",
                region, event_id)
            
            if not row:
                return None, None
            return row[0], row[1]

    async def add_event(self, region, event_id, event_title, banner, event_type, start, end, results, stories):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute("""
            INSERT INTO event_v1 VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, region, event_id, event_title, banner, event_type, 
            datetime.utcfromtimestamp(start), datetime.utcfromtimestamp(end),
            datetime.utcfromtimestamp(results))

            await c.executemany("""
            INSERT INTO event_story_v1 VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, stories)

    async def add_tiers(self, region, event_id, time, is_last, rows):
        async with self.pool.acquire() as c, c.transaction():
            await c.executemany("""
            INSERT INTO border_data_v1 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """, 
            ( (region, event_id, time, is_last, *r) for r in rows ))