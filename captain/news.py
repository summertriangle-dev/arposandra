import base64
import re
from datetime import datetime, timedelta
from html import unescape
from typing import Optional
from zoneinfo import ZoneInfo

from tornado.web import RequestHandler
from gettext import GNUTranslations

from . import pageutils
from .bases import BaseHTMLHandler, BaseAPIHandler
from .dispatch import DatabaseMixin, route

JP_OFFSET_FROM_UTC = 32400

class NewsBlindUtilMixin(RequestHandler):
    @staticmethod
    def format_blind_time(time: datetime, style: str, *, as_locale: GNUTranslations, as_timezone: Optional[ZoneInfo] = None):
        if as_timezone:
            time = time.astimezone(as_timezone)

        if style == "5":
            fmt = time.strftime(as_locale.gettext("kars.blindtime.fmt.time"))
            style = "time"
        elif style == "4":
            fmt = time.strftime(as_locale.gettext("kars.blindtime.fmt.fullshort"))
            style = "fullshort"
        elif style == "2":
            fmt = time.strftime(as_locale.gettext("kars.blindtime.fmt.date"))
            style = "date"
        else:
            fmt = time.strftime(as_locale.gettext("kars.blindtime.fmt.full"))
            style = "full"

        return fmt


@route(r"/news/?")
@route(r"/([a-z]+)/news/?")
class NewsList(BaseHTMLHandler, DatabaseMixin, NewsBlindUtilMixin):
    NUM_ITEMS_PER_PAGE = 20
    DM_TIMESTAMP_INSTR = re.compile("\uEC92(1|2|4|5)\\s+([0-9]+)")

    def item_display_title(self, region, title):
        t = unescape(title)
        if t.startswith("\uEC92"):
            locale = self.settings["static_strings"].get(self.database().news_database.server_news_language(region), "en")
            zone = ZoneInfo("Asia/Tokyo")
            t = self.DM_TIMESTAMP_INSTR.sub(
                lambda match: self.format_blind_time(
                    datetime.fromtimestamp(int(match.group(2)), tz=ZoneInfo("Etc/UTC")), 
                    match.group(1), as_locale=locale, as_timezone=zone),
                t[1:])

        return t 

    def convert_user_date(self, arg: str) -> Optional[datetime]:
        if arg.isdigit():
            return datetime.utcfromtimestamp(int(arg))
        
        try:
            isodate = datetime.strptime(arg, "%Y-%m-%d")
            return isodate + timedelta(days=1)
        except ValueError:
            return None

    async def get(self, region=None):
        if not region:
            server = self.database().news_database.validate_server_id(self.get_cookie("dsid", "jp"))
            self.redirect(f"/{server}/news/")
            return
        else:
            server = self.database().news_database.validate_server_id(region)

        before = None
        has_offset = True

        if before_arg := self.get_argument("before", None):
            before = self.convert_user_date(before_arg)
        
        if not before:
            before = datetime.utcnow()
            has_offset = False

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
class NewsSingle(BaseHTMLHandler, DatabaseMixin, NewsBlindUtilMixin):
    CARD_INCLUDE_INSTR = re.compile(r"<\?asi-include-card card-id:([0-9]+)\?>")
    TIMESTAMP_INSTR = re.compile(r"<\?asi-blind-ts t:(1|2|4|5);v:([0-9]+)\?>")
    DM_TIMESTAMP_INSTR = re.compile("\uEC92(1|2|4|5)\\s+([0-9]+)")
    JP_OFFSET_FROM_UTC = 32400

    def item_display_title(self, region, title):
        t = unescape(title)
        if t.startswith("\uEC92"):
            locale = self.settings["static_strings"].get(self.database().news_database.server_news_language(region), "en")
            zone = ZoneInfo("Asia/Tokyo")
            t = self.DM_TIMESTAMP_INSTR.sub(
                lambda match: self.format_blind_time(
                    datetime.fromtimestamp(int(match.group(2)), tz=ZoneInfo("Etc/UTC")), 
                    match.group(1), as_locale=locale, as_timezone=zone),
                t[1:])

        return t 

    def replace_card_inst(self, cards, match):
        cid = int(match.group(1))
        for card in cards:
            if card and card.id == cid:
                break
        else:
            card = None
        return self.render_string("uim_card_news_embed.html", card=card).decode("utf8")

    def replace_timestamp(self, locale, match):
        self.had_blinds = True
        t = match.group(1)

        zone = ZoneInfo("Asia/Tokyo")
        aware_dt = datetime.fromtimestamp(int(match.group(2)), tz=zone)
        def_str = self.format_blind_time(aware_dt, t, as_locale=locale, as_timezone=zone)

        if t == "5":
            style = "time"
        elif t == "4":
            style = "fullshort"
        elif t == "2":
            style = "date"
        else:
            style = "full"

        repl = f'<span class="kars-data-ts" data-orig-offset="{zone.utcoffset(aware_dt).total_seconds()},JST" data-ts="{match.group(2)}" data-style="{style}">{def_str}</span>'
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

        item_locale = self.settings["static_strings"].get(self.database().news_database.server_news_language(server), "en")
        item.card_refs = cards
        item.body_html = self.CARD_INCLUDE_INSTR.sub(
            lambda m: self.replace_card_inst(cards, m), item.body_html
        )
        item.body_html = self.TIMESTAMP_INSTR.sub(lambda x: self.replace_timestamp(item_locale, x), item.body_html)

        self.render(
            "news.html",
            news_items=[item],
            all_count=0,
            server=server,
            expand=True,
            has_next_page=False,
            has_offset=False,
            is_single=True,
            # FIXME: get rid of this
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
                return

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

        return self.render("leave_link.html", the_link=link)
