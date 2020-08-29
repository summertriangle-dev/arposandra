import os

if "NEW_RELIC_CONFIG_FILE" in os.environ:
    import newrelic.agent

    newrelic.agent.initialize()

import asyncio
import logging
import signal
import json
import sys

import tornado.ioloop
from asyncpg.exceptions import CannotConnectNowError

from captain.application import application


def get_master_version(tag=None):
    env = os.environ.get("AS_DATA_ROOT", ".")
    if not tag:
        tag = os.environ.get("AS_CANONICAL_REGION", None)

    if not tag:
        logging.warn("You need to set AS_CANONICAL_REGION. Defaulting to jp for now.")
        tag = "jp:ja"

    region, lang = tag.split(":", 1)

    root = os.path.join(env, region)
    try:
        with open(os.path.join(root, "astool_store.json"), "r") as memof:
            memo = json.load(memof)
        return os.path.join(root, "masters", memo["master_version"]), lang
    except (FileNotFoundError, KeyError):
        return root, lang


async def async_main():
    kr_addr = os.environ.get("AS_WEB_ADDR", "0.0.0.0")
    kr_port = int(os.environ.get("AS_WEB_PORT", 5000))
    debug = int(os.environ.get("AS_DEV", "0"))

    master_root, master_lang = get_master_version()
    logging.info("Master: %s", master_root)
    app = application(master_root, master_lang, debug)

    while True:
        try:
            await app.settings["db_coordinator"].prepare()
            break
        except (CannotConnectNowError, OSError) as e:
            logging.warning("Can't connect to database: %s", e)
        await asyncio.sleep(1)

    logging.info(f"Web server listening on {kr_addr}:{kr_port}")
    app.listen(kr_port, kr_addr, xheaders=True)


def handle_sigterm(signum, frame):
    runloop = tornado.ioloop.IOLoop.current()
    runloop.add_callback_from_signal(lambda: runloop.stop())


def main():
    debug = int(os.environ.get("AS_DEV", "0"))
    logging.basicConfig(
        format=f"%(asctime)s captain:  %(levelname)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(signal.signal, signal.SIGTERM, handle_sigterm)
    ioloop.add_future(asyncio.ensure_future(async_main()), lambda _: None)

    logging.debug("Entering the IOLoop...")
    ioloop.start()


if __name__ == "__main__":
    main()
