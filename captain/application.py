import os
import sys
import gettext
import logging
import json
from collections import namedtuple

from tornado.web import Application
from tornado import locale

from . import readonly_app_path
from .bases import DefaultHandler

import libcard2
from . import database
from . import dispatch
from . import pageutils
from . import dict_aggregator
from . import banners

# Start of handlers
from . import pages
from . import card_page
from . import tlinject
from . import news
from . import event_tracker
from . import search

# End of handlers


class DictionaryAccessProtocolImp(gettext.GNUTranslations):
    class Fallback(object):
        @classmethod
        def gettext(cls, k):
            return None

    def __init__(self, fp):
        super().__init__(fp)
        self.add_fallback(self.Fallback)

    def lookup_single_string(self, key):
        return self.gettext(key)


def static_strings():
    sd = {}
    catalog = readonly_app_path("gettext")
    for langcode in os.listdir(catalog):
        sd[langcode] = gettext.translation(
            "static", catalog, [langcode], DictionaryAccessProtocolImp
        )

    return sd


def find_astool_master_version(in_base):
    with open(os.path.join(in_base, "astool_store.json"), "r") as jsf:
        return json.load(jsf)["latest_complete_master"]


def create_dict_aggregator(master, language):
    choices = {}
    extra = os.environ.get("AS_EXTRA_DICTIONARIES")
    if extra:
        for tag in extra.split(";"):
            rgn_tag, lang_code, name = tag.split(":")
            region_root = os.path.join(os.environ.get("AS_DATA_ROOT", "."), rgn_tag)
            base = os.path.join(region_root, "masters", find_astool_master_version(region_root))
            logging.debug("Loading dictionary: %s", base)

            choices[lang_code] = dict_aggregator.Alternative(
                name, lang_code, libcard2.string_mgr.DictionaryAccess(base, lang_code)
            )

    fallback = libcard2.string_mgr.DictionaryAccess(master, language)
    return dict_aggregator.DictionaryAggregator(fallback, choices)


def create_more_masters():
    choices = {}
    extra = os.environ.get("AS_EXTRA_DICTIONARIES")
    if extra:
        for tag in extra.split(";"):
            rgn_tag = tag.split(":", 1)[0]
            if rgn_tag in choices:
                continue

            region_root = os.path.join(os.environ.get("AS_DATA_ROOT", "."), rgn_tag)
            base = os.path.join(region_root, "masters", find_astool_master_version(region_root))
            logging.debug("Loading sub master: %s", base)
            choices[rgn_tag] = libcard2.master.MasterDataLite(base)

    return choices


# Some private packages might require readonly_app_path - so we'll import this late.
from . import private
from . import chara_bdays


def application(master, language, debug):
    if os.environ.get("AS_TLINJECT_SECRET", ""):
        print("TLInject is enabled for this server.")

    if not os.environ.get("AS_COOKIE_SECRET"):
        raise ValueError("You need to set AS_COOKIE_SECRET in the environment.")

    locale.set_default_locale("en")
    locale.load_gettext_translations(readonly_app_path("gettext"), "tornado")
    strings = static_strings()
    db_coordinator = database.DatabaseCoordinator()

    have_preamble_extra = os.path.exists(readonly_app_path("webui", "t_preamble_extra.html"))
    have_footer_extra = os.path.exists(readonly_app_path("webui", "t_footer_extra.html"))

    vi_class = namedtuple("runtime_info_t", ("app_revision", "host_id"))
    runtime_info = vi_class(os.environ.get("AS_GIT_REVISION"), os.environ.get("AS_HOST_ID"))

    banner_manager = banners.BannerManager()
    banner_manager.by_date.update(chara_bdays.BIRTHDAYS)

    application = Application(
        dispatch.ROUTES,
        autoreload=debug,
        banner_manager=banner_manager,
        cookie_secret=os.environ.get("AS_COOKIE_SECRET"),
        db_coordinator=db_coordinator,
        debug=debug,
        feedback_link=os.environ.get("AS_FEEDBACK_URL"),
        have_footer_extra=have_footer_extra,
        have_preamble_extra=have_preamble_extra,
        image_server=os.environ.get("AS_IMAGE_SERVER"),
        master=libcard2.master.MasterData(master),
        more_masters=create_more_masters(),
        runtime_info=runtime_info,
        static_path=readonly_app_path("static"),
        static_strings=strings,
        string_access=create_dict_aggregator(master, language),
        template_path=readonly_app_path("webui"),
        tlinject_secret=os.environ.get("AS_TLINJECT_SECRET", "").encode("utf8"),
        ui_methods=pageutils.UI_METHODS,
        wds_host=os.environ.get("AS_WDS_HOST", "//localhost:5002") if debug else None,
        default_handler_class=DefaultHandler,
    )
    return application
