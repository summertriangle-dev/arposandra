import json
import sys
from collections import OrderedDict
from datetime import datetime
from typing import Iterable, List

from libcard2 import dataclasses
from tornado.locale import get_supported_locales
from tornado.web import RequestHandler

from . import pageutils
from .bases import BaseHTMLHandler, BaseAPIHandler
from .dispatch import DatabaseMixin, LanguageCookieMixin, route
from .models import card_tracking


@route("/")
class Slash(BaseHTMLHandler, LanguageCookieMixin):
    def get(self):
        self.render("home.html")


@route(r"/(cards|other)/")
class NavPageNoJS(BaseHTMLHandler):
    def get(self, where):
        if where == "cards":
            self.render("nav_cards_nojs.html")
        else:
            self.render("nav_other_nojs.html")


@route(r"/(?:idols|idol)/?")
@route(r"/idols/(unit)/([0-9]+)/?")
@route(r"/idols/(group)/([0-9]+)/?")
@route(r"/idols/(id)/([0-9]+)/?")
class IdolsRoot(BaseHTMLHandler, DatabaseMixin, LanguageCookieMixin):
    def base_member_preview_list(self, member: dataclasses.Member):
        if "base_member_preview_list" in member.user_info:
            lst = member.user_info["base_member_preview_list"]
            return lst, len(member.card_brief) - len(lst)

        r = []
        sr = []
        ur = []

        for card in reversed(member.card_brief):
            if card.rarity == 10:
                r.append(card)
            elif card.rarity == 20:
                sr.append(card)
            elif card.rarity == 30:
                ur.append(card)

        if len(member.card_brief) <= 9:
            lst = ur + sr + r
            member.user_info["base_member_preview_list"] = lst
            return lst, 0

        fill_r = min(len(r), 1)
        fill_sr = min(len(sr), 1)
        fill_ur = min(len(ur), 9 - fill_sr - fill_r)

        s = fill_ur + fill_sr + fill_r
        while s < 9:
            if len(sr) > fill_sr:
                fill_sr += 1
                s += 1
                continue
            if len(r) > fill_r:
                fill_r += 1
                s += 1
                continue

        lst = ur[:fill_ur] + sr[:fill_sr] + r[:fill_r]
        member.user_info["base_member_preview_list"] = lst
        return (
            lst,
            len(member.card_brief) - s,
        )

    def search_url_for_event(self, member: dataclasses.Member):
        return f"/cards/search#member={member.id}&source=[1,4,5,6,3]&_sort=-ordinal"

    def search_url_for_scoutable(self, member: dataclasses.Member):
        return f"/cards/search#member={member.id}&source=[2]&_sort=-ordinal"

    def get(self, specific=None, specific_value=None):
        show_all_card_icons = False

        if specific == "unit":
            members = self.master().lookup_member_list(subunit=int(specific_value))
        elif specific == "group":
            members = self.master().lookup_member_list(group=int(specific_value))
        elif specific == "id":
            members = [self.master().lookup_member_by_id(int(specific_value))]
            show_all_card_icons = True

            if not members[0]:
                self.set_status(404)
                self.render(
                    "error.html", message=self.locale.translate("ErrorMessage.ItemNotFound")
                )
                return
        else:
            members = self.master().lookup_member_list()

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

        self.render(
            "member_list.html",
            member_groups=groups,
            subpage_type=specific,
            show_all_card_icons=show_all_card_icons,
        )


@route("/lives")
class LiveRoot(BaseHTMLHandler, LanguageCookieMixin):
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
class LiveSingle(BaseHTMLHandler, LanguageCookieMixin):
    def get(self, live_id, _slug=None):
        song = self.settings["master"].lookup_song_difficulties(int(live_id))

        tlbatch = song.get_tl_set()
        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        self.render("song.html", songs=[song])


@route(r"/history/?")
@route(r"/history/([0-9]+)/?")
class HistoryRedirect(BaseHTMLHandler, DatabaseMixin, LanguageCookieMixin):
    def get(self, page=None):
        server = self.database().news_database.validate_server_id(self.get_cookie("dsid", None))
        if page is not None:
            self.redirect(f"/{server}/history/{page}/")
        else:
            self.redirect(f"/{server}/history/")


@route(r"/([a-z]+)/history/?")
@route(r"/([a-z]+)/history/([0-9]+)/?")
class CardHistory(BaseHTMLHandler, DatabaseMixin, LanguageCookieMixin):
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
class Accessories(BaseHTMLHandler, LanguageCookieMixin):
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
class Hirameku(BaseHTMLHandler, LanguageCookieMixin):
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
class ExperimentPage(BaseHTMLHandler, LanguageCookieMixin):
    def get(self):
        self.render("experiments.html")


@route(r"/([a-z]+)/story/(.+)")
class StoryViewerScaffold(BaseHTMLHandler, LanguageCookieMixin):
    def get(self, region, script):
        self.render(
            "story_scaffold.html",
            region=region,
            basename=script,
            asset_path=pageutils.sign_object(self, f"adv/{script}", "json"),
        )


@route(r"/api/v1/(?:[^/]*)/skill_tree/([0-9]+).json")
class APISkillTree(BaseAPIHandler):
    def get(self, i):
        items, shape, locks = self.settings["master"].lookup_tt(int(i))

        items["items"] = {
            k: (pageutils.image_url_reify(self, v[0], "png"), v[1])
            for k, v in items["items"].items()
        }

        self.write({"id": int(i), "tree": shape, "lock_levels": locks, "item_sets": items})


@route(r"/api/private/change_experiment_flags")
class APIChangeExperimentFlags(BaseAPIHandler):
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
class APILanguageMenu(BaseAPIHandler):
    def get(self):
        dicts = [
            {
                "code": self.settings["string_access"].master.language,
                "name": self.locale.translate("DefaultDictionaryName"),
            }
        ]
        dicts.extend(
            [
                {
                    "code": x.code,
                    "name": x.name,
                }
                for x in self.settings["string_access"].choices.values()
            ]
        )
        regions = ["jp", "en"]

        self.write(
            {"languages": list(get_supported_locales()), "dictionaries": dicts, "regions": regions}
        )


@route(r"/api/private/member_icon_list/([0-9]+)\.json")
class APIMemberIconList(BaseAPIHandler, DatabaseMixin):
    def get(self, member_id):
        member = self.master().lookup_member_by_id(int(member_id))
        payload = {
            "result": [
                [clite.ordinal, pageutils.card_icon_url(self, clite, clite.normal_appearance)]
                for clite in sorted(
                    reversed(member.card_brief), key=lambda x: x.rarity, reverse=True
                )
            ]
        }
        self.write(payload)
