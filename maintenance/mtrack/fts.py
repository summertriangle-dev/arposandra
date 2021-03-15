import os
import hashlib

from libcard2 import string_mgr
from libcard2.master import MasterData

LANG_TO_FTS_CONFIG = {
    "en": "card_fts_cfg_english",
}
TLINJECT_DUMMY_BASE_LANG = "en"


async def add_fts_string(lang: str, key: str, value: str, referent: int, connection):
    if not (fts_lang := LANG_TO_FTS_CONFIG.get(lang)):
        return

    hash = hashlib.sha224(value.encode("utf8"))
    await connection.execute(
        """
        INSERT INTO card_fts_v2 VALUES ($1, $2, $3, to_tsvector($6, $4), 'dict', $5)
        ON CONFLICT (langid, key, origin, referent_id) DO UPDATE
            SET terms = excluded.terms WHERE card_fts_v2.dupe != excluded.dupe
        """,
        lang,
        key,
        referent,
        value,
        hash.digest(),
        fts_lang,
    )


async def update_fts(
    lang: str, master: MasterData, dicts: string_mgr.DictionaryAccess, coordinator
):
    can_add_dictionary_tls = lang in LANG_TO_FTS_CONFIG

    async with coordinator.pool.acquire() as conn, conn.transaction():
        for id in master.card_ordinals_to_ids(master.all_ordinals()):
            card = master.lookup_card_by_id(id, use_cache=False)

            t_set = []
            if card.normal_appearance:
                t_set.append(card.normal_appearance.name)
            if card.idolized_appearance:
                t_set.append(card.idolized_appearance.name)

            for key in t_set:
                await conn.execute(
                    """
                    INSERT INTO card_fts_v2 VALUES ($1, $2, $3, NULL, 'tlinject', NULL)
                    ON CONFLICT (langid, key, origin, referent_id) DO NOTHING
                    """,
                    TLINJECT_DUMMY_BASE_LANG,
                    key,
                    card.id,
                )

            if can_add_dictionary_tls:
                strings = dicts.lookup_strings(t_set)
                for orig_key, value in strings.items():
                    await add_fts_string(lang, orig_key, value, card.id, conn)
