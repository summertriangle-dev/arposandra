import os

if "NEW_RELIC_CONFIG_FILE" in os.environ:
    import newrelic.agent

    newrelic.agent.initialize()

import logging

import tornado.ioloop

import skyfarer
import common_config as cfg


def other_masters():
    reg = os.environ.get("AS_EXTRA_REGIONS")
    if not reg:
        return {}

    ret = {}
    tag_pairs = [x.strip() for x in reg.split(";")]
    for t in tag_pairs:
        tag, lang = t.split(":")
        info = cfg.get_master_version(t)
        if os.path.exists(info[0]):
            ret[tag] = info

    return ret


def main():
    as_addr = os.environ.get("AS_ASSET_ADDR", "0.0.0.0")
    as_port = int(os.environ.get("AS_ASSET_PORT", 5001))

    debug = int(os.environ.get("AS_DEV", "0"))
    cfg.start_logging("asset", debug)
    master_root, master_lang = cfg.get_master_version()
    logging.info(f"Master: {master_root}")

    extras = other_masters()

    logging.info(f"Asset server listening on {as_addr}:{as_port}")
    skyfarer.application(master_root, master_lang, extras, debug).listen(
        as_port, as_addr, xheaders=True
    )

    logging.debug("Entering the IOLoop...")
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
