import os

if "NEW_RELIC_CONFIG_FILE" in os.environ:
    import newrelic.agent

    newrelic.agent.initialize()

import logging
import signal
import json

import tornado.ioloop

from skyfarer.web import application


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
        return os.path.join(root, "masters", memo["latest_complete_master"]), lang
    except (FileNotFoundError, KeyError):
        return root, lang


def other_masters():
    reg = os.environ.get("AS_EXTRA_REGIONS")
    if not reg:
        return {}

    ret = {}
    tag_pairs = [x.strip() for x in reg.split(";")]
    for t in tag_pairs:
        tag, lang = t.split(":")
        info = get_master_version(t)
        if os.path.exists(info[0]):
            ret[tag] = info

    return ret


def handle_sigterm(signum, frame):
    runloop = tornado.ioloop.IOLoop.current()
    runloop.add_callback_from_signal(lambda: runloop.stop())


def main():
    as_addr = os.environ.get("AS_ASSET_ADDR", "0.0.0.0")
    as_port = int(os.environ.get("AS_ASSET_PORT", 5001))

    debug = int(os.environ.get("AS_DEV", "0"))
    logging.basicConfig(
        format=f"%(asctime)s asset:  %(levelname)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )
    logging.getLogger("PIL").setLevel(logging.WARNING)

    master_root, master_lang = get_master_version()
    logging.info(f"Master: {master_root}")

    extras = other_masters()

    logging.info(f"Asset server listening on {as_addr}:{as_port}")
    application(master_root, master_lang, extras, debug).listen(as_port, as_addr, xheaders=True)

    runloop = tornado.ioloop.IOLoop.current()
    # We want to make sure the callback is only run if there's an ioloop.
    # So only register it after the ioloop has already started.
    runloop.add_callback(signal.signal, signal.SIGTERM, handle_sigterm)
    logging.debug("Entering the IOLoop...")
    runloop.start()


if __name__ == "__main__":
    main()
