import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
import pkg_resources
from collections import namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

import asyncpg
import plac

from captain.models import mine_models
from captain.models.indexer import db_expert, types
from libcard2 import string_mgr
from libcard2.master import MasterData
from maintenance.mtrack import newsminer, setminer, scripts as sql_scripts, fts

T_EVENT = 4
T_EVENT_GACHA = 3
T_GACHA = 2
T_BASE = 1

card_info_t = namedtuple("card_info_t", ("card_id", "ordinal", "probable_type"))

TAG_TO_MAIN_LANG = {"en": "en", "jp": "ja"}


class IndexerDBCoordinator(object):
    def __init__(self, connection_url: Optional[str]):
        self.connection_url = connection_url
        self.pool: "asyncpg.pool.Pool" = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url, min_size=1)
        init_schema = pkg_resources.resource_string("captain", "init_schema.sql").decode("utf8")
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(init_schema)

    async def drop_all_mtrack_tables(self):
        async with self.pool.acquire() as conn, conn.transaction():
            await conn.execute(
                """
                DROP TABLE IF EXISTS card_index_v1;
                DROP TABLE IF EXISTS card_index_v1__skill_minors;
                DROP TABLE IF EXISTS card_index_v1__release_dates;
                DROP TABLE IF EXISTS accessory_index_v1;
                DROP TABLE IF EXISTS accessory_index_v1__skill_minors;
                DROP TABLE IF EXISTS accessory_index_v1__release_dates;
                DROP TABLE IF EXISTS card_p_set_index_v1;
                DROP TABLE IF EXISTS card_p_set_index_v1__sort_dates;
                DROP TABLE IF EXISTS card_p_set_index_v1__card_ids;
                DROP TABLE IF EXISTS history_v5;
                DROP TABLE IF EXISTS history_v5__card_ids;
                DROP TABLE IF EXISTS history_v5__dates;
                """
            )
            logging.warning("All mtrack tables dropped.")


async def perform_master_ops(tag: str, lang: str, master: str, coordinator: IndexerDBCoordinator):
    can_update_base_data = tag == "jp"
    can_update_dict_langs = tag in ["en", "jp"]

    context = {}

    prefix = os.path.join(os.environ.get("ASTOOL_STORAGE", ""), tag, "masters", master)
    db = MasterData(prefix)
    daccess = string_mgr.DictionaryAccess(prefix, lang)

    if can_update_base_data:
        context["generated_sets"] = await update_card_index(lang, db, daccess, coordinator)
        await update_accessory_index(lang, db, daccess, coordinator)

    if can_update_dict_langs:
        await fts.update_fts(lang, db, daccess, coordinator)

    return context


async def update_card_index(
    lang: str,
    master: MasterData,
    dicts: string_mgr.DictionaryAccess,
    coordinator: IndexerDBCoordinator,
) -> List[mine_models.SetRecord]:
    cdb_expert = db_expert.PostgresDBExpert(mine_models.CardIndex)

    sets = {
        common_name: mine_models.SetRecord(
            common_name, rep, stype="song" if is_song else "same_name"
        )
        for rep, common_name, is_song in setminer.find_potential_set_names(dicts)
    }
    card_names = {}

    async with coordinator.pool.acquire() as conn:
        async with conn.transaction():
            await cdb_expert.create_tables(conn)

        async with conn.transaction():
            for id in master.card_ordinals_to_ids(master.all_ordinals()):
                card = master.lookup_card_by_id(id, use_cache=False)
                await cdb_expert.add_object(conn, card)

                if card.idolized_appearance:
                    card_names[card.id] = (card.idolized_appearance.name, card.ordinal)

        await setminer.generate_solo_sets(conn, master, dicts)

        # Group cards with the same idolized title.
        all_names = dicts.lookup_strings(x[0] for x in card_names.values())
        for (cid, (common_name, ordinal)) in card_names.items():
            set_name = all_names.get(common_name)
            if set_name in sets:
                # We want to end up with the same representative name every time.
                # Lowest ordinal is a good enough approximation for the first in
                # each series, so use that.
                sets[set_name].replace_representative(common_name, ordinal)
                sets[set_name].members.append(cid)

    return list(sets.values())


async def update_accessory_index(
    lang: str,
    master: MasterData,
    dicts: string_mgr.DictionaryAccess,
    coordinator: IndexerDBCoordinator,
):
    adb_expert = db_expert.PostgresDBExpert(mine_models.AccessoryIndex)

    async with coordinator.pool.acquire() as conn:
        async with conn.transaction():
            await adb_expert.create_tables(conn)

        async with conn.transaction():
            for accessory in master.lookup_all_accessories():
                await adb_expert.add_object(conn, accessory)


async def insert_timeline(expert, conn, events):
    # Use a temporary table with only the new history entries so we don't
    # query the entire list again for set ref updates.
    prefix = "mtrack_multi_op_"
    await expert.create_tables(conn, temporary=True, temp_prefix=prefix)

    for event in events:
        await expert.add_object(conn, event, prefix=prefix)

    await conn.execute(sql_scripts.update_card_release_dates(prefix))

    # Now do the real insert.
    for event in events:
        await expert.add_object(conn, event)


@plac.pos("tag", "Server ID")
@plac.pos("mv", "Master version to interrogate. Pass '-' to skip (only run newsminer)")
@plac.flg("quiet", "Silence logging")
@plac.flg("clear_history", "Clear history before running newsminer", abbrev="x")
@plac.flg(
    "clear_history_hard",
    "Clear everything before running index and newsminer. Dangerous!!",
    abbrev="X",
)
async def main(
    tag: str,
    mv: str,
    quiet: bool = False,
    clear_history: bool = False,
    clear_history_hard: bool = False,
):
    cloc = time.monotonic()

    if not quiet:
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger("captain.models.indexer.db_expert.sql").setLevel(logging.INFO)

    coordinator = IndexerDBCoordinator(os.environ.get("AS_POSTGRES_DSN"))
    await coordinator.create_pool()
    hist_expert = db_expert.PostgresDBExpert(mine_models.HistoryIndex)
    set_expert = db_expert.PostgresDBExpert(mine_models.SetIndex)
    accessory_expert = db_expert.PostgresDBExpert(mine_models.AccessoryIndex)

    need_reinit = False
    if clear_history_hard:
        await coordinator.drop_all_mtrack_tables()
        need_reinit = True

    async with coordinator.pool.acquire() as conn:
        await hist_expert.create_tables(conn)
        await set_expert.create_tables(conn)
        await accessory_expert.create_tables(conn)

    generated_sets: List[mine_models.SetRecord] = []

    if mv != "-":
        context = await perform_master_ops(tag, TAG_TO_MAIN_LANG[tag], mv, coordinator)
        generated_sets = context.get("generated_sets", generated_sets)

    logging.debug("Master import done in %s ms", (time.monotonic() - cloc) * 1000)
    cloc = time.monotonic()

    async with coordinator.pool.acquire() as conn:
        if clear_history:
            need_reinit = True
            async with conn.transaction():
                await conn.execute("DELETE FROM history_v5 where serverid=$1", tag)

        events = await newsminer.assemble_timeline(conn, tag)

        async with conn.transaction():
            if need_reinit:
                logging.warning("Added pre-history entries. Be careful!")
                pre_events = newsminer.prepare_old_evt_entries(tag)
                events = pre_events + events

            for set_ in setminer.filter_sets_against_history(generated_sets, events, tag == "jp"):
                await set_expert.add_object(conn, set_, overwrite=False)

            if events:
                await insert_timeline(hist_expert, conn, events)

    logging.debug("NewsMiner import done in %s ms", (time.monotonic() - cloc) * 1000)
    cloc = time.monotonic()

    async with coordinator.pool.acquire() as conn:
        await setminer.update_ordinal_sets(conn, set_expert)
        await conn.execute(sql_scripts.update_set_sort_table())
        await conn.execute(sql_scripts.update_hist_event_link())

    logging.debug("SetMiner import done in %s ms", (time.monotonic() - cloc) * 1000)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(plac.call(main))
    loop.close()
