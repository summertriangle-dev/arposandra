import os
import hmac
import hashlib
from datetime import datetime


class TLInjectContext(object):
    LANG_CODE_TO_FTS_CONFIG = {"en": "english"}

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.secret = os.environ.get("AS_TLINJECT_SECRET").encode("utf8")
        self.supported_languages = []

    @staticmethod
    def batches(iterable, groups_of=500):
        if len(iterable) <= groups_of:
            yield iterable
            return

        start = 0
        while 1:
            group = iterable[start : start + groups_of]
            if not group:
                break
            yield group
            start = start + groups_of

    async def prepare(self):
        async with self.coordinator.pool.acquire() as c:
            self.supported_languages = [
                lang for lang, in await c.fetch("SELECT langid FROM tlinject_languages_v1")
            ]
            self.supported_languages.sort(key=lambda x: 0 if x == "en" else 1)

    def is_language_valid(self, langid):
        return langid in self.supported_languages

    def is_assr_valid(self, key, assr):
        calc_assr = hmac.new(self.secret, key.encode("utf8"), hashlib.sha224).digest()[:12]
        return hmac.compare_digest(assr, calc_assr)

    async def write_string(self, lang, key, string, sender):
        if lang not in self.supported_languages:
            return (1, "Translations for this language are not accepted at this time.")

        if string is not None:
            string = string.strip()
            if len(string) < 2:
                return (1, "Please submit a longer string.")

        async with self.coordinator.pool.acquire() as c, c.transaction():
            now = datetime.utcnow()
            await c.execute(
                "INSERT INTO tlinject_v1 VALUES($1, $2, $3, $4, $5)",
                lang,
                key,
                string,
                sender,
                now,
            )
            await c.execute(
                "INSERT INTO tlinject_cache_v1 VALUES ($1, $2, $3) ON CONFLICT (langid, key) DO UPDATE SET translated = excluded.translated",
                lang,
                key,
                string,
            )
            if cfg := self.LANG_CODE_TO_FTS_CONFIG.get(lang):
                hash = hashlib.sha224(string.encode("utf8")).digest()
                await c.execute(
                    """
                    UPDATE card_fts_v2 SET terms = to_tsvector($5, $3), dupe = $4
                    WHERE origin = 'tlinject' AND key = $2 AND langid = $1""",
                    lang,
                    key,
                    string,
                    hash,
                    cfg,
                )

        return (0, "OK")

    async def read_strings(self, lang, sset):
        if not sset:
            return (0, {})

        if not self.is_language_valid(lang):
            return (1, "Translations for this language are not available at this time.")

        ret = {}

        async with self.coordinator.pool.acquire() as c:
            for page in self.batches(list(sset)):
                params = ",".join(f"${i}" for i in range(2, 2 + len(page)))
                q = f"""
                    SELECT key, translated FROM tlinject_cache_v1 
                    WHERE langid = $1 AND key IN ({params}) AND translated IS NOT NULL"""
                strings = await c.fetch(q, lang, *page)
                for record in strings:
                    ret[record["key"]] = record["translated"]

        return (0, ret)
