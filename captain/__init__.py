import os
import sys
import configparser
from collections import namedtuple

from tornado.web import Application
from tornado import locale

from . import database
from . import dispatch
from . import pages
from . import card_page
from . import pageutils
from . import tlinject
from . import news
from . import card_tracking
import libcard2


def readonly_app_path(*p):
    return os.path.join(os.path.dirname(__file__), *p)


def create_runtime_info():
    vi_class = namedtuple("runtime_info_t", ("app_revision", "host_id", "python_version"))
    return vi_class(os.environ.get("AS_GIT_REVISION"), os.environ.get("AS_HOST_ID"), sys.version)


def static_strings():
    cfg = configparser.ConfigParser()
    cfg.add_section("Strings")
    try:
        with open(readonly_app_path("strings.ini"), "r") as sf:
            cfg.read_file(sf)
    except FileNotFoundError:
        pass

    return {k: v for k, v in cfg.items("Strings")}


def application(master, debug):
    if os.environ.get("AS_TLINJECT_SECRET", ""):
        print("TLInject is enabled for this server.")

    locale.set_default_locale("en")
    locale.load_gettext_translations(readonly_app_path("gettext"), "tornado")
    strings = static_strings()
    db_coordinator = database.DatabaseCoordinator()

    application = Application(
        dispatch.ROUTES,
        db_coordinator=db_coordinator,
        master=libcard2.master.MasterData(master),
        string_access=libcard2.string_mgr.DictionaryAccess(master),
        image_server=os.environ.get("AS_IMAGE_SERVER"),
        tlinject_context=tlinject.TLInjectContext(db_coordinator),
        news_context=news.NewsDatabase(db_coordinator),
        card_tracking=card_tracking.CardTrackingDatabase(db_coordinator),
        template_path=readonly_app_path("webui"),
        runtime_info=create_runtime_info(),
        tlinject_secret=os.environ.get("AS_TLINJECT_SECRET", "").encode("utf8"),
        ui_methods=pageutils.UI_METHODS,
        static_path=readonly_app_path("static"),
        static_strings=strings,
        debug=debug,
        autoreload=debug,
    )
    return application