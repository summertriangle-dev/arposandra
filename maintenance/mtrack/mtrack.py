import os
from datetime import date
from collections import namedtuple
import json
import logging
import sys
import asyncio
import time

import asyncpg

from libcard2.master import MasterData

T_EVENT = 4
T_EVENT_GACHA = 3
T_GACHA = 2
T_BASE = 1

card_info_t = namedtuple("card_info_t", ("card_id", "ordinal", "probable_type"))


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)

    async def init_models(self):
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(
                """
                CREATE TABLE IF NOT EXISTS card_tracking_v1 (
                    serverid varchar(8),
                    card_id int,
                    card_ordinal int,
                    firstseen_master varchar(32),
                    probably_type int,
                    norm_date date,
                    PRIMARY KEY (serverid, card_id)
                );
                """
            )

    async def insert_cards(self, server_id, card_infos, master, norm_date):
        async with self.pool.acquire() as c, c.transaction():
            await c.executemany(
                "INSERT INTO card_tracking_v1 VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT DO NOTHING",
                (
                    (server_id, c.card_id, c.ordinal, master, c.probable_type, norm_date)
                    for c in card_infos
                ),
            )


def guess_type(id):
    fd = id // 100000000
    return fd


async def main():
    cloc = time.monotonic()

    logging.basicConfig(level=logging.INFO)
    tag = sys.argv[1]
    mvs = sys.argv[2:]

    pg = DatabaseConnection()
    await pg.create_pool()
    await pg.init_models()

    for mv in mvs:
        mtime = os.path.getmtime(
            os.path.join(os.environ.get("ASTOOL_STORAGE"), tag, "masters", mv, "masterdata.db")
        )
        db = MasterData(os.path.join(os.environ.get("ASTOOL_STORAGE"), tag, "masters", mv))
        all_cards = db.do_not_use_get_all_card_briefs()
        await pg.insert_cards(
            tag,
            (card_info_t(c.id, c.ordinal, guess_type(c.id)) for c in all_cards),
            mv,
            date.fromtimestamp(mtime),
        )

    print("done in", time.monotonic() - cloc)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
