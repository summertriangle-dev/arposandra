import hmac
import hashlib
import base64
import binascii
import os
import time
import json
import sys
import calendar
import re
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import List, Union
from html import unescape

import asyncpg
from tornado.web import RequestHandler

from .dispatch import route, LanguageCookieMixin
from . import pageutils
from libcard2.dataclasses import Card

JP_OFFSET_FROM_UTC = 32400


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
    def __init__(self, coordinator):
        self.coordinator = coordinator

    async def get_news_items(self, for_server, before_time, limit):
        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(
                """SELECT news_id, title, thumbnail, ts, internal_category, NULL, card_refs 
                    FROM news_v2 WHERE ts < $1 AND (visible = TRUE OR internal_category IN (2, 3))
                    ORDER BY ts DESC, news_id LIMIT $2""",
                before_time,
                limit,
            )

        return [NewsItem(*i, json.loads(crefs) if crefs else []) for *i, crefs in items]

    async def get_only_card_carrying_news_items(self, for_server, before_time, limit):
        async with self.coordinator.pool.acquire() as c:
            items = await c.fetch(
                """SELECT news_id, title, thumbnail, ts, internal_category, NULL, card_refs
                    FROM news_v2 WHERE ts < $1 AND internal_category IN (2, 3) AND card_refs IS NOT NULL
                    ORDER BY ts DESC, news_id LIMIT $2""",
                before_time,
                limit,
            )

        return [NewsItem(*i, json.loads(crefs)) for *i, crefs in items]

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


@route("/news/?")
@route("/([a-z]+)/news/?")
class NewsList(LanguageCookieMixin):
    NUM_ITEMS_PER_PAGE = 20

    async def get(self, region=None):
        before = self.get_argument("before", None)
        has_offset = False
        if not before:
            before = datetime.utcnow()
        else:
            try:
                before = datetime.utcfromtimestamp(int(before))
                has_offset = True
            except ValueError:
                before = datetime.utcnow()

        server = region or "jp"
        count = await self.settings["news_context"].count_news_items(server)
        items = await self.get_items(server, before, self.NUM_ITEMS_PER_PAGE + 1)
        has_next_page = len(items) > self.NUM_ITEMS_PER_PAGE
        self.resolve_cards(items)

        self.render(
            "news.html",
            news_items=items[: self.NUM_ITEMS_PER_PAGE],
            all_count=count,
            server=server,
            expand=False,
            has_next_page=has_next_page,
            has_offset=has_offset,
            is_single=False,
            time_offset=JP_OFFSET_FROM_UTC,
            show_ts_msg=False,
        )

    async def get_items(self, server, before, nmax):
        cookie = self.cookies.get("nfm", None)
        if cookie and cookie.value == "1":
            return await self.settings["news_context"].get_only_card_carrying_news_items(
                server, before, nmax
            )

        return await self.settings["news_context"].get_news_items(server, before, nmax)

    def resolve_cards(self, items):
        for item in items:
            if not item.card_refs:
                continue
            cards = self.settings["master"].lookup_multiple_cards_by_id(item.card_refs)
            item.card_refs = [c for c in cards if c]


@route("/([a-z]+)/news/([0-9]+)")
class NewsSingle(LanguageCookieMixin):
    CARD_INCLUDE_INSTR = re.compile(r"<\?asi-include-card card-id:([0-9]+)\?>")
    TIMESTAMP_INSTR = re.compile(r"<\?asi-blind-ts t:(1|2|4|5);v:([0-9]+)\?>")
    JP_OFFSET_FROM_UTC = 32400

    def replace_card_inst(self, cards, match):
        cid = int(match.group(1))
        for card in cards:
            if card and card.id == cid:
                break
        else:
            card = None
        return self.render_string("uim_card_news_embed.html", card=card).decode("utf8")

    def replace_timestamp(self, match):
        # FIXME: needs to detect EN server timestamps
        self.had_blinds = True
        t = match.group(1)
        if t == "1":
            fmt = datetime.fromtimestamp(int(match.group(2))).strftime("%Y年%m月%d日 %H:%M")
            style = "full"
        elif t == "5":
            fmt = datetime.fromtimestamp(int(match.group(2))).strftime("%H:%M")
            style = "time"
        elif t == "4":
            fmt = datetime.fromtimestamp(int(match.group(2))).strftime("%m月%d日 %H:%M")
            style = "fullshort"
        elif t == "2":
            fmt = datetime.fromtimestamp(int(match.group(2))).strftime("%m月%d日")
            style = "date"

        repl = f'<span class="kars-data-ts" data-orig-offset="{JP_OFFSET_FROM_UTC},JST" data-ts="{match.group(2)}" data-style="{style}">{fmt}</span>'
        return repl

    async def get(self, server, nid):
        item = await self.settings["news_context"].get_full_text(server, int(nid))
        cards = [
            c for c in self.settings["master"].lookup_multiple_cards_by_id(item.card_refs) if c
        ]

        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(tlbatch)
        self.had_blinds = False

        item.card_refs = cards
        item.body_html = self.CARD_INCLUDE_INSTR.sub(
            lambda m: self.replace_card_inst(cards, m), item.body_html
        )
        item.body_html = self.TIMESTAMP_INSTR.sub(self.replace_timestamp, item.body_html)

        self.render(
            "news.html",
            news_items=[item],
            all_count=0,
            server=server,
            expand=True,
            has_next_page=False,
            has_offset=False,
            is_single=True,
            time_offset=JP_OFFSET_FROM_UTC,
            show_ts_msg=self.had_blinds,
        )


@route("/api/private/ii")
class InlineImageResolver(RequestHandler):
    def get(self):
        imp = self.get_argument("p", None)
        if imp is None:
            self.set_status(400)
            self.write({"error": "A URL must be provided."})
            return

        asset_path = self.settings["master"].lookup_inline_image(imp)

        if asset_path:
            self.redirect(pageutils.image_url_reify(self, asset_path, "jpg"))
        else:
            self.set_status(404)
            self.write({"error": "The image could not be resolved."})


@route("/api/private/intersitial")
class NewsLinkDerefer(LanguageCookieMixin):
    def get(self):
        imp = self.get_argument("p", None)
        if imp is None:
            self.set_status(400)
            self.write({"error": "A URL must be provided."})
            return

        try:
            link = base64.urlsafe_b64decode((imp + "====").encode("ascii")).decode("utf8")
        except ValueError:
            self.set_status(404)
            self.write({"error": "Invalid mask link."})
            return

        if not (link.startswith("http:") or link.startswith("https:")):
            self.set_status(404)
            self.write({"error": "Invalid mask link."})
            ascii

        return self.render("leave_link.html", the_link=link)
