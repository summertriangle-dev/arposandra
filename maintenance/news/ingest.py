import json
import os
from datetime import datetime

import asyncpg
import pkg_resources


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def init_models(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)
        init_schema = pkg_resources.resource_string("captain", "init_schema.sql").decode("utf8")
        async with self.pool.acquire() as c, c.transaction():
            try:
                await c.execute(init_schema)
            except asyncpg.UniqueViolationError:
                pass

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

    async def update_visibility(self, server_id, vis_list):
        tmp_table_name = f"vis_{server_id}"
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                f"CREATE TEMPORARY TABLE {tmp_table_name}(notice_id int, visible bool) ON COMMIT DROP"
            )
            await c.copy_records_to_table(tmp_table_name, records=[(id, True) for id in vis_list])
            await c.execute("UPDATE news_v2 SET visible = FALSE WHERE serverid = $1", server_id)
            await c.execute(
                f"""UPDATE news_v2 SET visible = {tmp_table_name}.visible FROM {tmp_table_name}
                WHERE {tmp_table_name}.notice_id = news_v2.news_id AND serverid = $1""",
                server_id,
            )

    async def all_dt(self):
        async with self.pool.acquire() as c, c.transaction():
            return await c.fetch("SELECT serverid, dt_id, body_dm FROM dt_v1")

    async def get_dt_epoch(self, server_id):
        async with self.pool.acquire() as c:
            t = await c.fetchrow(
                "SELECT next_ts FROM dt_v1 WHERE serverid = $1 ORDER BY next_ts DESC LIMIT 1",
                server_id,
            )
            if not t:
                return datetime.utcfromtimestamp(0)
            return t[0]

    async def add_dt(self, server_id, dtid, ts, next_ts, title, body_dm, body_html, char_refs):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                """INSERT INTO dt_v1 VALUES ($1, $2, $3, $4, $5, $6, $7) ON CONFLICT (serverid, dt_id)
                    DO UPDATE SET next_ts = excluded.next_ts, body_html = excluded.body_html,
                    body_dm = excluded.body_dm""",
                server_id,
                dtid,
                ts,
                next_ts,
                title,
                body_html,
                body_dm,
            )
            await c.executemany(
                "INSERT INTO dt_char_refs_v1 VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                ((server_id, dtid, x) for x in char_refs),
            )

    async def update_dt(self, server_id, dt_id, body, char_refs):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                "UPDATE dt_v1 SET body_html=$1 WHERE serverid=$2 AND dt_id=$3",
                body,
                server_id,
                dt_id,
            )
            await c.execute(
                "DELETE FROM dt_char_refs_v1 WHERE serverid=$1 AND dt_id=$2", server_id, dt_id
            )
            await c.executemany(
                "INSERT INTO dt_char_refs_v1 VALUES ($1, $2, $3) ON CONFLICT DO NOTHING",
                ((server_id, dt_id, x) for x in char_refs),
            )
