import os

if "NEW_RELIC_CONFIG_FILE" in os.environ:
    import newrelic.agent

    newrelic.agent.initialize()

import asyncio
import logging
import signal

import tornado.ioloop
from asyncpg.exceptions import CannotConnectNowError

import captain
import common_config as cfg


async def async_main(app, kr_addr, kr_port):
    while True:
        try:
            await app.settings["db_coordinator"].prepare()
            break
        except (CannotConnectNowError, OSError) as e:
            logging.warning("Can't connect to database: %s", e)
        await asyncio.sleep(1)

    # FIXME: move this
    await app.settings["tlinject_context"].init_models()

    logging.info(f"Web server listening on {kr_addr}:{kr_port}")
    app.listen(kr_port, kr_addr, xheaders=True)


def handle_sigterm(signum, frame):
    runloop = tornado.ioloop.IOLoop.current()
    runloop.add_callback_from_signal(lambda: runloop.stop())


def main():
    kr_addr = os.environ.get("AS_WEB_ADDR", "0.0.0.0")
    kr_port = int(os.environ.get("AS_WEB_PORT", 5000))

    debug = int(os.environ.get("AS_DEV", "0"))
    cfg.start_logging("web", debug)
    master_root, master_lang = cfg.get_master_version()
    logging.info(f"Master: {master_root}")

    ioloop = tornado.ioloop.IOLoop.current()
    ioloop.add_callback(signal.signal, signal.SIGTERM, handle_sigterm)
    ioloop.add_future(
        asyncio.ensure_future(
            async_main(captain.application(master_root, master_lang, debug), kr_addr, kr_port)
        ),
        lambda _: None,
    )

    logging.debug("Entering the IOLoop...")
    ioloop.start()


if __name__ == "__main__":
    main()
