import os
import json
import logging

def start_logging(who, debug):
    logging.basicConfig(format=f"%(asctime)s {who}:  %(levelname)s: %(message)s",
        level=logging.DEBUG if debug else logging.INFO)

def get_master_version():
    env = os.environ.get("AS_DATA_ROOT", ".")
    try:
        with open(os.path.join(env, "astool_store.json"), "r") as memof:
            memo = json.load(memof)
        return os.path.join(env, "masters", memo["master_version"])
    except (FileNotFoundError, KeyError):
        return env

