import hmac
import hashlib
import base64
import binascii
import os
import time
import json
import sys
from datetime import datetime

import asyncpg
from tornado.web import RequestHandler

from .dispatch import route
from . import pageutils


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


class TLInjectContext(object):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self.secret = os.environ.get("AS_TLINJECT_SECRET").encode("utf8")
        self.supported_languages = []

    async def init_models(self):
        async with self.coordinator.pool.acquire() as c:
            async with c.transaction():
                await c.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tlinject_v1 (
                        langid varchar(8),
                        key text,
                        translated text,
                        sender varchar(48),
                        ts timestamp
                    );
                    CREATE TABLE IF NOT EXISTS tlinject_cache_v1 (
                        langid varchar(8),
                        key text,
                        translated text,
                        PRIMARY KEY (langid, key)
                    );
                    CREATE TABLE IF NOT EXISTS tlinject_languages_v1 (
                        langid varchar(8) primary key
                    );

                    INSERT INTO tlinject_languages_v1 VALUES ('en') ON CONFLICT DO NOTHING;
                    """
                )

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

        return (0, "OK")

    async def read_strings(self, lang, sset):
        if not sset:
            return (0, {})

        if not self.is_language_valid(lang):
            return (1, "Translations for this language are not available at this time.")

        ret = {}

        async with self.coordinator.pool.acquire() as c:
            for page in batches(list(sset)):
                params = ",".join(f"${i}" for i in range(2, 2 + len(page)))
                q = f"""
                    SELECT key, translated FROM tlinject_cache_v1 
                    WHERE langid = $1 AND key IN ({params}) AND translated IS NOT NULL"""
                strings = await c.fetch(q, lang, *page)
                for record in strings:
                    ret[record["key"]] = record["translated"]

        return (0, ret)


@route(r"/api/private/tlinject/([a-z_A-Z]+)/strings.json")
class TLInjectReadAPI(RequestHandler):
    PER_REQUEST_HARD_LIMIT = 500

    async def post(self, lang):
        if not self.settings["tlinject_context"].is_language_valid(lang):
            self.set_status(400)
            self.write({"error": "Translations for this language are not available at this time."})
            return

        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            self.write({"error": "Input must be provided as a JSON list."})
            return
        else:
            if not isinstance(load, list):
                self.set_status(400)
                self.write({"error": "Input must be provided as a JSON list."})
                return

        unique = set(load)
        if len(unique) > self.PER_REQUEST_HARD_LIMIT:
            self.set_status(400)
            self.write({"error": "Request fewer strings."})
            return

        error, sd = await self.settings["tlinject_context"].read_strings(lang, unique)
        if error != 0:
            self.set_status(400)
            self.write({"error": sd})
        else:
            self.set_status(200)
            self.write({"results": sd})


@route(r"/api/private/tlinject/([a-z_A-Z]+)/submit.json")
class TLInjectWriteAPI(RequestHandler):
    async def post(self, lang):
        try:
            load = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            self.write({"error": "Input must be provided as a JSON dict."})
            return
        else:
            if not isinstance(load, dict):
                self.set_status(400)
                self.write({"error": "Input must be provided as a JSON dict."})
                return

        key = load.get("key")
        assr = load.get("assr")
        tstring = load.get("translated")

        if not all((key, assr)):
            self.set_status(400)
            self.write({"error": "You're missing input."})

        try:
            assr = base64.urlsafe_b64decode(assr)
        except (ValueError, TypeError):
            self.set_status(400)
            self.write({"error": "The assurance value is invalid."})
            return

        if not self.settings["tlinject_context"].is_assr_valid(key, assr):
            self.set_status(400)
            self.write({"error": "The assurance value is invalid."})
            return

        status, message = await self.settings["tlinject_context"].write_string(
            lang, key, tstring, self.request.remote_ip
        )
        if status != 0:
            self.set_status(400)
            self.write({"error": message})
        else:
            self.set_status(200)
            self.write({"results": {key: tstring}})
