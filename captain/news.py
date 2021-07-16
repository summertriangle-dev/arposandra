import base64
import binascii
import calendar
import hashlib
import hmac
import json
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from html import unescape
from typing import List, Union

import asyncpg
from tornado.web import RequestHandler

from . import pageutils
from .bases import BaseHTMLHandler, BaseAPIHandler
from .dispatch import DatabaseMixin, route

JP_OFFSET_FROM_UTC = 32400


@route(r"/news/?")
@route(r"/([a-z]+)/news/?")
class NewsList(BaseHTMLHandler, DatabaseMixin):
    NUM_ITEMS_PER_PAGE = 20

    async def get(self, region=None):
        if not region:
            server = self.database().news_database.validate_server_id(self.get_cookie("dsid", "jp"))
            self.redirect(f"/{server}/news/")
            return
        else:
            server = self.database().news_database.validate_server_id(region)

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

        count = await self.database().news_database.count_news_items(server)
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
        return await self.database().news_database.get_news_items(server, before, nmax)

    def resolve_cards(self, items):
        for item in items:
            if not item.card_refs:
                continue
            cards = self.master().lookup_multiple_cards_by_id(item.card_refs, briefs_ok=True)
            item.card_refs = [c for c in cards if c]


@route(r"/([a-z]+)/news/([0-9]+)")
class NewsSingle(BaseHTMLHandler, DatabaseMixin):
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
        item = await self.database().news_database.get_full_text(server, int(nid))
        cards = [
            c for c in self.settings["master"].lookup_multiple_cards_by_id(item.card_refs) if c
        ]

        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )
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


@route(r"/api/private/ii")
class InlineImageResolver(BaseAPIHandler):
    def get(self):
        imp = self.get_argument("p", None)
        if imp is None:
            self.set_status(400)
            self.write({"error": "A URL must be provided."})
            return

        region = self.get_argument("n", None)
        if region and region != "jp":
            sub = self.settings["more_masters"].get(region)
            if not sub:
                self.set_status(404)
                self.write({"error": "No such region."})
            asset_path = sub.lookup_inline_image(imp)
        else:
            asset_path = self.settings["master"].lookup_inline_image(imp)
            region = None

        if asset_path:
            self.redirect(pageutils.image_url_reify(self, asset_path, "jpg", region))
        else:
            self.set_status(404)
            self.write({"error": "The image could not be resolved."})


@route(r"/api/private/intersitial")
class NewsLinkDerefer(BaseHTMLHandler):
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
