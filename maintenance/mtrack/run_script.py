import asyncio
import logging
import os
import sys

import asyncpg
import plac


@plac.opt("file", "Script file (default stdin)")
async def main(file: str = None):
    logging.basicConfig(level=logging.INFO)
    connection = await asyncpg.connect(os.environ.get("AS_POSTGRES_DSN"))

    if file:
        with open(file, "r") as script:
            cmds = script.read()
    else:
        cmds = sys.stdin.read()

    ret = await connection.execute(cmds)
    print(ret)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(plac.call(main))
    loop.close()
