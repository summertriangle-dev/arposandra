import sys
import json
import asyncio
import logging
from unittest import mock
from datetime import datetime

import ingest
import dm_parse
import theatre_parse


async def main():
    db = ingest.DatabaseConnection()
    await db.init_models()

    num = 0
    for server, post_id, post_body in await db.all_posts():
        body_html, c_refs, _ = dm_parse.dm_to_html(post_body.encode("utf8"))
        await db.update_post(server, post_id, body_html, c_refs)
        num += 1
    logging.info("Reparsed %d news items.", num)

    num = 0
    for server, dt_id, dt_body in await db.all_dt():
        synth = dm_parse.dm_to_html_v2(dt_body.encode("utf8"), theatre_parse.TheatreScriptWalkState)
        await db.update_dt(server, dt_id, synth.get_json(), synth.char_refs)
        num += 1
    logging.info("Reparsed %d daily convos.", num)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
