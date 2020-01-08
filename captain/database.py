import os

import asyncpg


class DatabaseCoordinator(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def prepare(self):
        if not self.pool:
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
                CREATE TABLE IF NOT EXISTS card_tracking_v1 (
                    serverid varchar(8),
                    card_id int,
                    card_ordinal int,
                    firstseen_master varchar(32),
                    probably_type int,
                    norm_date date,
                    PRIMARY KEY (serverid, card_id)
                );"""
            )

