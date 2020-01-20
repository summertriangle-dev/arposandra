import sys
import json
import asyncio
from unittest import mock
from datetime import datetime
import logging
import time

import models

ESTART = 1578290400
ECLOSE = 1579068000
ERESULT = 1579068000 + 10800

ESIM_ID = 100001
ESIM_REGION = "jp"


async def create_fake_event_record(db):
    await db.add_event(
        ESIM_REGION, ESIM_ID, None, "abc", "mining", ESTART, ECLOSE, ERESULT, [],
    )


async def get_event_border(db: models.DatabaseConnection):
    if not await db.have_event_info(ESIM_REGION, ESIM_ID):
        logging.info("Need to generate the event description")
        await create_fake_event_record(db)

    PT = [
        100,
        500,
        1000,
        2000,
        3000,
        4000,
        5000,
        6000,
        7000,
        8000,
        9000,
        10000,
        20000,
        30000,
        40000,
        50000,
        60000,
        70000,
        80000,
        90000,
        100000,
    ]

    VO = [
        100,
        500,
        1000,
        2000,
        3000,
        4000,
        5000,
        6000,
        7000,
        8000,
        9000,
    ]
    for dp in range(ESTART, ECLOSE, 3600):
        observe_time = datetime.utcfromtimestamp(dp)
        logging.info("T = %s", observe_time)

        to_db = []
        for tier in PT:
            step = (dp - ESTART) // 3600
            ep_now = (100000 - tier) + step * 1000
            to_db.append(("points", ep_now, 1, tier))

        for tier in VO:
            step = (dp - ESTART) // 3600
            ep_now = (100000 - tier) + step * 30000
            to_db.append(("voltage", ep_now, 1, tier))

        await db.add_tiers(ESIM_REGION, ESIM_ID, observe_time, False, to_db, [])


async def main():
    logging.basicConfig(level=logging.INFO)
    db = models.DatabaseConnection()
    await db.init_models()
    await get_event_border(db)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
