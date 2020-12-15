import logging
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from tornado.web import RequestHandler

from . import pageutils

JST = timezone(timedelta(hours=9))


class BannerDefn(object):
    def template_name(self, handler: RequestHandler) -> str:
        return ""

    def template_args(self, handler: RequestHandler) -> dict:
        return {}


class BannerManager(object):
    def banners(self, handler: RequestHandler):
        date = datetime.utcnow().astimezone(JST)
        bday_key = (date.month, date.day)

        if handler.get_cookie("as_test_banner_check_date") == "yes":
            bday_key = (4, 19)

        if bday_key in BIRTHDAYS:
            return [BIRTHDAYS[bday_key]]


@dataclass
class Birthday(BannerDefn):
    char_id: int
    date: datetime
    advice: str = None

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


# TODO: move this somewhere else
BIRTHDAYS = {
    (8, 3): Birthday(1, datetime(3048, 8, 3, tzinfo=JST)),
    (10, 21): Birthday(2, datetime(3048, 10, 21, tzinfo=JST)),
    (9, 12): Birthday(3, datetime(3048, 9, 12, tzinfo=JST)),
    (3, 15): Birthday(4, datetime(3048, 3, 15, tzinfo=JST)),
    (11, 1): Birthday(5, datetime(3048, 11, 1, tzinfo=JST)),
    (4, 19): Birthday(6, datetime(3048, 4, 19, tzinfo=JST)),
    (6, 9): Birthday(7, datetime(3048, 6, 9, tzinfo=JST)),
    (1, 17): Birthday(8, datetime(3048, 1, 17, tzinfo=JST)),
    (7, 22): Birthday(9, datetime(3048, 7, 22, tzinfo=JST)),
    (8, 1): Birthday(101, datetime(3048, 8, 1, tzinfo=JST)),
    (9, 19): Birthday(102, datetime(3048, 9, 19, tzinfo=JST)),
    (2, 10): Birthday(103, datetime(3048, 2, 10, tzinfo=JST)),
    (1, 1): Birthday(104, datetime(3048, 1, 1, tzinfo=JST)),
    (4, 17): Birthday(105, datetime(3048, 4, 17, tzinfo=JST)),
    (7, 13): Birthday(106, datetime(3048, 7, 13, tzinfo=JST)),
    (3, 4): Birthday(107, datetime(3048, 3, 4, tzinfo=JST)),
    (6, 13): Birthday(108, datetime(3048, 6, 13, tzinfo=JST)),
    (9, 21): Birthday(109, datetime(3048, 9, 21, tzinfo=JST)),
    (3, 1): Birthday(201, datetime(3048, 3, 1, tzinfo=JST)),
    (1, 23): Birthday(202, datetime(3048, 1, 23, tzinfo=JST)),
    (4, 3): Birthday(203, datetime(3048, 4, 3, tzinfo=JST)),
    (6, 29): Birthday(204, datetime(3048, 6, 29, tzinfo=JST)),
    (5, 30): Birthday(205, datetime(3048, 5, 30, tzinfo=JST)),
    (12, 16): Birthday(206, datetime(3048, 12, 16, tzinfo=JST)),
    (8, 8): Birthday(207, datetime(3048, 8, 8, tzinfo=JST)),
    (2, 5): Birthday(208, datetime(3048, 2, 5, tzinfo=JST)),
    (11, 13): Birthday(209, datetime(3048, 11, 13, tzinfo=JST)),
    (10, 5): Birthday(210, datetime(3048, 10, 5, tzinfo=JST)),
}
