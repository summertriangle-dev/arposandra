import os
import pkg_resources
import hmac
import hashlib
from datetime import datetime, timezone
from collections import defaultdict

import asyncpg

from .models import event_model, news_model, tlinject_model, card_tracking


class DatabaseCoordinator(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

        self.event_tracker = event_model.EventTrackingDatabase(self)
        self.news_database = news_model.NewsDatabase(self)
        self.tlinject_database = tlinject_model.TLInjectContext(self)
        self.card_tracker = card_tracking.CardTrackingDatabase(self)

    async def prepare(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(dsn=self.connection_url, min_size=1)

        init_schema = pkg_resources.resource_string("captain", "init_schema.sql").decode("utf8")
        async with self.pool.acquire() as c, c.transaction():
            await c.execute(init_schema)

        await self.tlinject_database.prepare()
