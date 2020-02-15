import os
from datetime import date
from collections import namedtuple
import json
import logging
import sys
import asyncio
import time
import sqlite3

import asyncpg

from libcard2.master import MasterData
import maintenance.mtrack.indexer
import maintenance.mtrack.db_expert

T_EVENT = 4
T_EVENT_GACHA = 3
T_GACHA = 2
T_BASE = 1

card_info_t = namedtuple("card_info_t", ("card_id", "ordinal", "probable_type"))


class IndexerDBCoordinator(object):
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url)


async def main():
    cloc = time.monotonic()

    logging.basicConfig(level=logging.INFO)
    tag = sys.argv[1]
    mvs = sys.argv[2:]

    conn = IndexerDBCoordinator(os.environ.get("AS_POSTGRES_DSN"))
    await conn.create_pool()

    expert = maintenance.mtrack.db_expert.PostgresDBExpert(
        maintenance.mtrack.indexer.CardIndex, conn.pool
    )
    await expert.create_tables()

    for mv in mvs:
        mtime = os.path.getmtime(
            os.path.join(os.environ.get("ASTOOL_STORAGE"), tag, "masters", mv, "masterdata.db")
        )
        db = MasterData(os.path.join(os.environ.get("ASTOOL_STORAGE"), tag, "masters", mv))

        async with conn.pool.acquire() as c, c.transaction():
            for id in db.card_ordinals_to_ids(db.all_ordinals()):
                card = db.lookup_card_by_id(id)
                await expert.add_object(c, card)

    print("done in", time.monotonic() - cloc)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
