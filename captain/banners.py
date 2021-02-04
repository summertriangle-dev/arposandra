import logging
import random
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from typing import Protocol, Optional, List

from tornado.web import RequestHandler

from . import pageutils

JST = timezone(timedelta(hours=9))


class BannerDefn(Protocol):
    def template_name(self, handler: RequestHandler) -> str:
        return ""

    def template_args(self, handler: RequestHandler) -> dict:
        return {}


class BannerManager(object):
    def __init__(self):
        self.by_date = {}

    def banners(self, handler: RequestHandler) -> Optional[List[BannerDefn]]:
        date = datetime.utcnow().astimezone(JST)
        bday_key = (date.month, date.day)
        if bday_key in self.by_date:
            return [self.by_date[bday_key]]

        if random.randint(1, 6) == 1:
            return [DonationBanner()]

        return None


class DonationBanner(object):
    def template_name(self, handler: RequestHandler):
        return "uim_banner_donation.html"

    def template_args(self, handler: RequestHandler):
        return {}


@dataclass
class BirthdayBanner(object):
    char_id: int
    date: datetime

    def template_name(self, handler: RequestHandler):
        return "uim_banner_birthday.html"

    def template_args(self, handler: RequestHandler):
        h = handler.settings["master"]
        if self.char_id > 0:
            member = h.lookup_member_by_id(self.char_id)

        date_fmt = self.date.strftime(
            handler.locale.translate("Banner.Birthday.ShortDateStrftimeFormat")
        )
        name = pageutils.tlinject_static(handler, member.name_romaji, escape=False)

        if handler.locale.code.startswith("en"):
            name = name.split(" ")[0]

        return {
            "banner_color": "#db6ba7",
            "text_color": "#fcfcfc",
            "text": handler.locale.translate("Banner.Birthday.MessageFor{name}On{date}").format(
                name=name, date=date_fmt
            ),
            "icon": pageutils.image_url_reify(handler, member.thumbnail_image_asset_path, "png"),
        }
