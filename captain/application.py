import os
import sys
import gettext
import logging
import json
from collections import namedtuple

from tornado.web import Application
from tornado import locale

from . import readonly_app_path

from . import database
from . import dispatch
from . import pages
from . import card_page
from . import pageutils
from . import tlinject
from . import news
from . import card_tracking
from . import event_tracker
from . import dict_aggregator
import libcard2

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
        return json.load(jsf)["master_version"]


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


def application(master, language, debug):
    if os.environ.get("AS_TLINJECT_SECRET", ""):
        print("TLInject is enabled for this server.")

    locale.set_default_locale("en")
    locale.load_gettext_translations(readonly_app_path("gettext"), "tornado")
    strings = static_strings()
    db_coordinator = database.DatabaseCoordinator()

    have_preamble_extra = os.path.exists(readonly_app_path("webui", "t_preamble_extra.html"))
    have_footer_extra = os.path.exists(readonly_app_path("webui", "t_footer_extra.html"))

    vi_class = namedtuple("runtime_info_t", ("app_revision", "host_id"))
    runtime_info = vi_class(os.environ.get("AS_GIT_REVISION"), os.environ.get("AS_HOST_ID"))

    application = Application(
        dispatch.ROUTES,
        db_coordinator=db_coordinator,
        master=libcard2.master.MasterData(master),
        more_masters=create_more_masters(),
        string_access=create_dict_aggregator(master, language),
        image_server=os.environ.get("AS_IMAGE_SERVER"),
        tlinject_context=tlinject.TLInjectContext(db_coordinator),
        news_context=news.NewsDatabase(db_coordinator),
        card_tracking=card_tracking.CardTrackingDatabase(db_coordinator),
        event_tracking=event_tracker.EventTrackingDatabase(db_coordinator),
        template_path=readonly_app_path("webui"),
        runtime_info=runtime_info,
        tlinject_secret=os.environ.get("AS_TLINJECT_SECRET", "").encode("utf8"),
        ui_methods=pageutils.UI_METHODS,
        static_path=readonly_app_path("static"),
        static_strings=strings,
        debug=debug,
        autoreload=debug,
        wds_host=os.environ.get("AS_WDS_HOST", "//localhost:5002") if debug else None,
        have_preamble_extra=have_preamble_extra,
        have_footer_extra=have_footer_extra,
    )
    return application
