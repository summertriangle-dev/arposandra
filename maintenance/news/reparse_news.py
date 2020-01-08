import sys
import json
import asyncio
from unittest import mock
from datetime import datetime

import ingest
import dm_parse

async def main():
    db = ingest.DatabaseConnection()
    num = 0
    for server, post_id, post_body in await db.all_posts():
        body_html, c_refs, _ = dm_parse.dm_to_html(post_body.encode("utf8"))
        await db.update_post(server, post_id, body_html, c_refs)
        num += 1
    print("Reparsed", num, "news items.")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()
