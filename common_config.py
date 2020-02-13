import os
import json
import logging


def start_logging(who, debug):
    logging.basicConfig(
        format=f"%(asctime)s {who}:  %(levelname)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO,
    )


def get_master_version():
    env = os.environ.get("AS_DATA_ROOT", ".")
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

