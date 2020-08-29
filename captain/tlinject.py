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

from .dispatch import route, DatabaseMixin
from . import pageutils


@route(r"/api/private/tlinject/([a-z_A-Z]+)/strings.json")
class TLInjectReadAPI(DatabaseMixin):
    PER_REQUEST_HARD_LIMIT = 500

    async def post(self, lang):
        if not self.database().tlinject_database.is_language_valid(lang):
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

        error, sd = await self.database().tlinject_database.read_strings(lang, unique)
        if error != 0:
            self.set_status(400)
            self.write({"error": sd})
        else:
            self.set_status(200)
            self.write({"results": sd})


@route(r"/api/private/tlinject/([a-z_A-Z]+)/submit.json")
class TLInjectWriteAPI(DatabaseMixin):
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

        if not self.database().tlinject_database.is_assr_valid(key, assr):
            self.set_status(400)
            self.write({"error": "The assurance value is invalid."})
            return

        status, message = await self.database().tlinject_database.write_string(
            lang, key, tstring, self.request.remote_ip
        )
        if status != 0:
            self.set_status(400)
            self.write({"error": message})
        else:
            self.set_status(200)
            self.write({"results": {key: tstring}})
