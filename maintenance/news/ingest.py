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
                CREATE TABLE IF NOT EXISTS news_v2 (
                    serverid varchar(8),
                    news_id int,
                    thumbnail varchar(16),
                    title text,
                    ts timestamp,
                    internal_category int,
                    body_html text,
                    body_dm text,
                    card_refs text,
                    visible bool,
                    PRIMARY KEY (serverid, news_id)
                );

                CREATE TABLE IF NOT EXISTS dt_v1 (
                    serverid varchar(8),
                    dt_id int,
                    ts timestamp,
                    next_ts timestamp,
                    title text,
                    body_html text,
                    body_dm text,
                    PRIMARY KEY (serverid, dt_id)
                );

                CREATE TABLE IF NOT EXISTS dt_char_refs_v1 (
                    serverid varchar(8),
                    dt_id int,
                    char_id int,
                    FOREIGN KEY (serverid, dt_id) REFERENCES dt_v1 (serverid, dt_id)
                        ON UPDATE CASCADE ON DELETE CASCADE
                );
                """
            )

    async def get_epoch(self, server_id):
        async with self.pool.acquire() as c:
            t = await c.fetchrow(
                "SELECT ts FROM news_v2 WHERE serverid = $1 ORDER BY ts DESC LIMIT 1", server_id
            )
            if not t:
                return datetime.utcfromtimestamp(0)
            return t[0]

    async def insert_notice(
        self, server_id, nid, title, ts, cat, thumb, body_dm, body_html, card_refs
    ):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                "INSERT INTO news_v2 VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, FALSE) ON CONFLICT DO NOTHING",
                server_id,
                nid,
                thumb,
                title,
                ts,
                cat,
                body_html,
                body_dm,
                json.dumps(card_refs) if card_refs else None,
            )

    async def all_posts(self):
        async with self.pool.acquire() as c, c.transaction():
            return await c.fetch("SELECT serverid, news_id, body_dm FROM news_v2")

    async def update_post(self, server_id, nid, body_html, card_refs):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                "UPDATE news_v2 SET body_html=$1, card_refs=$2 WHERE serverid=$3 AND news_id=$4",
                body_html,
                json.dumps(card_refs) if card_refs else None,
                server_id,
                nid,
            )

    async def update_visibility(self, vis_list):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                "CREATE TEMPORARY TABLE vis(notice_id int, visible bool) ON COMMIT DROP"
            )
            await c.copy_records_to_table("vis", records=[(id, True) for id in vis_list])
            await c.execute("UPDATE news_v2 SET visible = FALSE")
            await c.execute(
                "UPDATE news_v2 SET visible = vis.visible FROM vis WHERE vis.notice_id = news_v2.news_id"
            )

    async def get_dt_epoch(self, server_id):
        async with self.pool.acquire() as c:
            t = await c.fetchrow(
                "SELECT next_ts FROM dt_v1 WHERE serverid = $1 ORDER BY next_ts DESC LIMIT 1",
                server_id,
            )
            if not t:
                return datetime.utcfromtimestamp(0)
            return t[0]

    async def add_dt(self, server_id, dtid, ts, next_ts, title, body_dm, body_html):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                "INSERT INTO dt_v1 VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT DO NOTHING",
                server_id,
                dtid,
                ts,
                next_ts,
                title,
                body_html,
                body_dm,
            )
