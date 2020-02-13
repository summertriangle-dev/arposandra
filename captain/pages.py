from collections import OrderedDict
from tornado.web import RequestHandler

from .dispatch import route, LanguageCookieMixin
from . import pageutils
import libcard2.localization


@route("/")
class Slash(LanguageCookieMixin):
    def get(self):
        self.render("home.html")


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


@route(r"/api/private/search/bootstrap.json")
class APISearchBootstrap(RequestHandler):
    def gen_sd(self):
        sd = libcard2.localization.skill_describer_for_locale(self.locale.code)
        desc_fmt_args = {"var": "", "let": "", "end": "", "value": "X"}

        word_set = {}
        for skill_id, formatter in sd.skill_effect.data.items():
            if callable(formatter):
                wl = formatter(**desc_fmt_args)
            else:
                wl = formatter.format(**desc_fmt_args)

    def get(self):
        return
