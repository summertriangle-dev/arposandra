import calendar
import json
from datetime import datetime
from dataclasses import dataclass
from typing import List, Union
from html import unescape

from libcard2.dataclasses import Card


@dataclass
class NewsItem(object):
    id: int
    title: str
    thumbnail_asset_path: str
    date: datetime
    category: int
    body_html: str
    card_refs: List[Union[Card, int]]

    def timestamp(self):
        return calendar.timegm(self.date.utctimetuple())

    def display_title(self):
        return unescape(self.title)


class NewsDatabase(object):
    SERVER_IDS = ["jp", "en"]

    def __init__(self, coordinator):
        self.coordinator = coordinator

    def validate_server_id(self, server_id):
        if server_id not in self.SERVER_IDS:
            return self.SERVER_IDS[0]
        return server_id

    async def get_news_items(self, for_server, before_time, limit):
        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(
                """SELECT news_id, title, thumbnail, ts, internal_category, NULL, card_refs
                    FROM news_v2 WHERE ts < $1 AND visible = TRUE
                    AND serverid=$3 ORDER BY ts DESC, news_id LIMIT $2""",
                before_time,
                limit,
                for_server,
            )

        return [NewsItem(*i, json.loads(crefs) if crefs else []) for *i, crefs in items]

    async def count_news_items(self, for_server):
        async with self.coordinator.pool.acquire() as c:
            items = await c.fetchrow("SELECT COUNT(0) FROM news_v2 WHERE serverid=$1", for_server)

        return items[0]

    async def get_full_text(self, for_server, news_id):
        async with self.coordinator.pool.acquire() as c:
            item = await c.fetchrow(
                "SELECT news_id, title, thumbnail, ts, internal_category, body_html, card_refs FROM news_v2 WHERE serverid=$1 AND news_id=$2",
                for_server,
                news_id,
            )

        return NewsItem(*item[:-1], json.loads(item[-1]) if item[-1] else [])
