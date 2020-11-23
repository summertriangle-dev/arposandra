import json
from collections import OrderedDict
from tornado.web import RequestHandler
from tornado.locale import get_supported_locales
from typing import Iterable
from datetime import datetime

from .dispatch import route, LanguageCookieMixin, DatabaseMixin
from . import pageutils
from .models import card_tracking
import libcard2.localization
import sys


@route("/")
class Slash(LanguageCookieMixin):
    def get(self):
        self.render("home.html")


@route(r"/(cards|other)/")
class NavPageNoJS(RequestHandler):
    def get(self, where):
        if where == "cards":
            self.render("nav_cards_nojs.html")
        else:
            self.render("nav_other_nojs.html")


@route("/(?:idols|idol)/?")
@route("/idols/(unit)/([0-9]+)")
@route("/idols/(group)/([0-9]+)")
class IdolsRoot(LanguageCookieMixin):
    def get(self, specific=None, specific_value=None):
        nav_crumb_level = 0
        if specific == "unit":
            members = self.settings["master"].lookup_member_list(subunit=int(specific_value))
            nav_crumb_level = 2
        elif specific == "group":
            members = self.settings["master"].lookup_member_list(group=int(specific_value))
            nav_crumb_level = 1
        else:
            members = self.settings["master"].lookup_member_list()

        tlbatch = set()
        groups = OrderedDict()
        for mem in members:
            if mem.group_name in groups:
                groups[mem.group_name].append(mem)
            else:
                groups[mem.group_name] = [mem]
            tlbatch.update(mem.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        self.render("member_list.html", member_groups=groups, nav_crumb_level=nav_crumb_level)


@route("/lives")
class LiveRoot(LanguageCookieMixin):
    def get(self):
        songs = self.settings["master"].lookup_song_list()

        tlbatch = set()
        groups = OrderedDict()
        for s in songs:
            if s.member_group_name in groups:
                groups[s.member_group_name].append(s)
            else:
                groups[s.member_group_name] = [s]
            tlbatch.update(s.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )
        self.render("song_list.html", live_groups=groups, nav_crumb_level=0)


@route("/live(?:s)?/([0-9]+)(/.*)?")
class LiveSingle(LanguageCookieMixin):
    def get(self, live_id, _slug=None):
        song = self.settings["master"].lookup_song_difficulties(int(live_id))

        tlbatch = song.get_tl_set()
        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        self.render("song.html", songs=[song])


@route(r"/history/?")
@route(r"/history/([0-9]+)/?")
class HistoryRedirect(DatabaseMixin, LanguageCookieMixin):
    def get(self, page=None):
        server = self.database().news_database.validate_server_id(self.get_cookie("dsid", None))
        if page is not None:
            self.redirect(f"/{server}/history/{page}/")
        else:
            self.redirect(f"/{server}/history/")


@route(r"/([a-z]+)/history/?")
@route(r"/([a-z]+)/history/([0-9]+)/?")
class CardHistory(DatabaseMixin, LanguageCookieMixin):
    VALID_CATEGORIES: List[str] = []

    async def get(self, server_id, page=None):
        server = self.database().news_database.validate_server_id(server_id)

        pageno = 0
        if page:
            pageno = max(int(page) - 1, 0)

        now = datetime.utcnow()
        his = await self.database().card_tracker.get_history_entries(
            server, None, pageno, n_entries=20
        )

        count = await self.database().card_tracker.get_history_entry_count(server, None)

        self.resolve_cards(his)
        self.render(
            "history.html",
            releases=his,
            current_page=pageno + 1,
            page_count=int((count / 20) + 1),
            server=server,
            current_time=now,
        )

    def url_for_page(self, pageno: int):
        args = []
        tag = self.path_args[0]
        tag = self.database().news_database.validate_server_id(tag)

        cat = self.get_argument("type", None)
        if cat in self.VALID_CATEGORIES:
            args.append(f"type={cat}")

        if pageno > 1:
            page_frag = f"{pageno}/"
        else:
            page_frag = ""

        qs = ("?" + "&".join(args)) if args else ""
        return f"/{tag}/history/{page_frag}{qs}"

    def resolve_cards(self, items: Iterable[card_tracking.HistoryRecord]):
        for item in items:
            for key in list(item.feature_card_ids.keys()):
                cards = self.master().lookup_multiple_cards_by_id(
                    item.feature_card_ids[key], briefs_ok=True
                )
                item.feature_card_ids[key] = [c for c in cards if c]


@route("/accessory_skills")
class Accessories(LanguageCookieMixin):
    def get(self):
        skills = self.settings["master"].lookup_all_accessory_skills()
        tlbatch = set()
        for skill in skills:
            tlbatch.update(skill.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )
        self.render("accessories.html", skills=skills)


@route("/hirameku_skills")
class Hirameku(LanguageCookieMixin):
    def get(self):
        skills = self.settings["master"].lookup_all_hirameku_skills()
        skills.sort(key=lambda x: (x.levels[0][2], x.rarity))

        tlbatch = set()
        for skill in skills:
            tlbatch.update(skill.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )
        self.render("accessories.html", skills=skills)


@route("/experiments")
class ExperimentPage(LanguageCookieMixin):
    def get(self):
        self.render("experiments.html")


@route(r"/([a-z]+)/story/(.+)")
class StoryViewerScaffold(LanguageCookieMixin):
    def get(self, region, script):
        self.render(
            "story_scaffold.html",
            region=region,
            basename=script,
            asset_path=pageutils.sign_object(self, f"adv/{script}", "json"),
        )


@route(r"/api/v1/(?:[^/]*)/skill_tree/([0-9]+).json")
class APISkillTree(RequestHandler):
    def get(self, i):
        items, shape, locks = self.settings["master"].lookup_tt(int(i))

        items["items"] = {
            k: (pageutils.image_url_reify(self, v[0], "png"), v[1])
            for k, v in items["items"].items()
        }

        self.write({"id": int(i), "tree": shape, "lock_levels": locks, "item_sets": items})


@route(r"/api/private/change_experiment_flags")
class APIChangeExperimentFlags(RequestHandler):
    FLAG_SHOW_DEV_TEXT = 1 << 1

    def post(self):
        try:
            req = json.loads(self.request.body.decode("utf8"))
        except ValueError:
            self.set_status(400)
            return

        try:
            cookie = self.get_secure_cookie("cs_fflg_v2", max_age_days=1000000)
            current_flags = int(cookie or 0)
        except ValueError:
            current_flags = 0

        password = req.get("password")
        if password == "yaldabaoth":
            current_flags ^= self.FLAG_SHOW_DEV_TEXT
            if current_flags & self.FLAG_SHOW_DEV_TEXT:
                ret_s = "You will now see debug text in places that have it."
            else:
                ret_s = "You will no longer see debug text in places that had it."
        else:
            self.set_status(400)
            return

        self.set_secure_cookie("cs_fflg_v2", str(current_flags), expires_days=1000000)
        self.write({"message": ret_s})
        return


@route(r"/api/private/langmenu.json")
class APILanguageMenu(RequestHandler):
    def get(self):
        dicts = [
            {
                "code": self.settings["string_access"].master.language,
                "name": self.locale.translate("DefaultDictionaryName"),
            }
        ]
        dicts.extend(
            [
                {"code": x.code, "name": x.name,}
                for x in self.settings["string_access"].choices.values()
            ]
        )
        regions = ["jp", "en"]

        self.write(
            {"languages": list(get_supported_locales()), "dictionaries": dicts, "regions": regions}
        )

