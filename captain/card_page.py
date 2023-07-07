import base64
import hashlib
import hmac
import random
import re
from datetime import datetime, timezone
from typing import Iterable, Optional, Tuple, Dict, List, Any, cast

from tornado.web import RequestHandler

from libcard2.dataclasses import Card, Member

from .bases import BaseHTMLHandler, BaseAPIHandler
from .dispatch import DatabaseMixin, route
from .models import card_tracking
from .models.indexer import db_expert, types
from .models.mine_models import CardIndex
from .pageutils import (
    get_as_secret,
    tlinject_static,
    image_url_reify,
    card_icon_url,
    get_skill_describer,
)


def card_spec(spec: str) -> list:
    ret = []
    unique = set()
    for s in spec.split(","):
        try:
            v = int(s)
        except ValueError:
            continue
        if v in unique:
            continue
        ret.append(v)
        unique.add(v)
    return ret


@route(r"/cards/(random|(?:[0-9,]+))(/.*)?")
class CardPageRedirect(BaseHTMLHandler):
    def get(self, spec, end):
        self.redirect(f"/card/{spec}{end or ''}", permanent=True)


@route(r"/card/(random|(?:[0-9,]+))(/.*)?")
class CardPage(BaseHTMLHandler, DatabaseMixin):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self._tlinject_base = ({}, set())

    def find_sets(self, sets, card_id):
        # This should be replaced with a faster method
        for s in sets:
            for cid in s.card_refs:
                if card_id == cid.id:
                    yield s

    def resolve_related_sets(self, related_sets):
        tlbatch = set()

        # Put event sets at top
        related_sets.sort(key=lambda x: -1 if x.set_type == x.T_EVENT else 0)
        for cardset in related_sets:
            if cardset.is_systematic():
                self._tlinject_base[0][cardset.representative] = CardGallery.make_synthetic_name(
                    self, cardset.representative
                )

            # FIXME: hack
            if cardset.representative.startswith("k."):
                tlbatch.add(cardset.representative)

            if cardset.set_type == cardset.T_EVENT:
                briefs = self.master().lookup_multiple_cards_by_id(
                    [cref.id for cref in cardset.card_refs], briefs_ok=True
                )
                clean = []
                for ref, clite in zip(cardset.card_refs, briefs):
                    if clite:
                        ref.card = clite
                        clean.append(ref)

                clean.sort(key=lambda x: (-x.card.rarity, x.card.ordinal))
                cardset.card_refs = clean

        self.translate_strings(tlbatch)
        return related_sets

    def translate_strings(self, batch):
        s0, s1 = self.settings["string_access"].lookup_strings(
            batch, self.get_user_dict_preference()
        )
        self._tlinject_base[0].update(s0)
        self._tlinject_base[1].update(s1)

    async def get(self, ordinal, _):
        if ordinal == "random":
            where = random.choice(self.settings["master"].all_ordinals())
            self.redirect(f"/card/{where}")
            return

        ordinals = card_spec(ordinal)

        cards = self.settings["master"].lookup_multiple_cards_by_id(
            self.settings["master"].card_ordinals_to_ids(ordinals)
        )
        cards = [c for c in cards if c]

        tlbatch = set()
        for card in cards:
            if card:
                tlbatch.update(card.get_tl_set())

        sets = self.resolve_related_sets(
            await self.database().card_tracker.get_containing_card_sets([c.id for c in cards])
        )
        self.translate_strings(tlbatch)

        if len(cards) == 0:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return
        elif len(cards) == 1:
            ct = self.locale.translate("#{card_no}: {idol_name}").format(
                idol_name=tlinject_static(self, cards[0].member.name_romaji, escape=False),
                card_no=cards[0].ordinal,
            )
        else:
            ct = self.locale.translate("{num_cards} cards").format(num_cards=len(cards))

        self.render("cards.html", cards=cards, custom_title=ct, related_sets=sets, og_context={})


@route(r"/cards/by_idol/([0-9]+)(/.*)?")
class CardPageByMemberID(CardPage, DatabaseMixin):
    async def get(self, member_id, _):
        member = self.settings["master"].lookup_member_by_id(member_id)

        if not member:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return

        card_ids = [cl.id for cl in reversed(member.card_brief)]
        cards = self.settings["master"].lookup_multiple_cards_by_id(card_ids)

        tlbatch = member.get_tl_set()
        for card in cards:
            tlbatch.update(card.get_tl_set())
        self.translate_strings(tlbatch)

        sets = self.resolve_related_sets(
            await self.database().card_tracker.get_containing_card_sets([c.id for c in cards])
        )

        self.render(
            "cards.html",
            cards=cards,
            custom_title=self.locale.translate("Cards of {idol_name}").format(
                idol_name=tlinject_static(self, member.name_romaji, escape=False)
            ),
            related_sets=sets,
            og_context={"type": "member", "member": member},
        )


class CardThumbnailProviderMixin(object):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if RequestHandler not in cls.__mro__:
            raise TypeError("This mixin needs to be used with a subclass of RequestHandler.")

    def initialize(self, *args, **kwargs):
        self.thumb_cache = {}

    def thumbnail(self, appearance: Card.Appearance, size: int, axis: str, fmt: str):
        h = cast(RequestHandler, self)
        first = (
            base64.urlsafe_b64encode(appearance.image_asset_path.encode("utf8"))
            .decode("ascii")
            .rstrip("=")
        )
        key = f"thumb/{size}{axis}/{first}"

        if key in self.thumb_cache:
            return self.thumb_cache[key]

        assr_b = hmac.new(get_as_secret(), key.encode("utf8"), hashlib.sha224).digest()[:10]
        assr = base64.urlsafe_b64encode(assr_b).decode("ascii").rstrip("=")
        isr = h.settings["image_server"]
        signed = f"{isr}/thumb/{size}{axis}/{first}/{assr}.{fmt}"

        self.thumb_cache[key] = signed
        return signed


@route(r"/cards/sets/?")
@route(r"/cards/sets/([0-9]+)/?")
class CardGallery(BaseHTMLHandler, DatabaseMixin, CardThumbnailProviderMixin):
    # The largest known subunit size (QU4RTZ). This is checked so we don't treat
    # subunit costume sets as group sets.
    ALL_MEMBER_SET_THRES = 4
    FILL_SET_TYPES = [
        card_tracking.CardSetRecord.T_DEFAULT,
        card_tracking.CardSetRecord.T_SONG,
        card_tracking.CardSetRecord.T_FES,
        card_tracking.CardSetRecord.T_PARTY,
    ]
    VALID_CATEGORIES = {
        "other": card_tracking.CardSetRecord.T_DEFAULT,
        "event": card_tracking.CardSetRecord.T_EVENT,
        "song": card_tracking.CardSetRecord.T_SONG,
        "fes": card_tracking.CardSetRecord.T_FES,
        "pickup": card_tracking.CardSetRecord.T_PICKUP,
        "party": card_tracking.CardSetRecord.T_PARTY,
    }
    SAME_GROUP_ORD_TYPES = [
        card_tracking.CardSetRecord.T_FES,
        card_tracking.CardSetRecord.T_PICKUP,
        card_tracking.CardSetRecord.T_PARTY,
    ]

    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        CardThumbnailProviderMixin.initialize(self)
        self._tlinject_base = ({}, set())
        self.tl_batch = set()

    # FIXME: We should be implementing this in SQL.
    def custom_sort_key(self, aset: card_tracking.CardSetRecord):
        if aset.set_type == card_tracking.CardSetRecord.T_DEFAULT:
            return (aset.max_date(), 1)
        elif aset.set_type == card_tracking.CardSetRecord.T_EVENT:
            return (aset.max_date(), 10)
        elif aset.set_type == card_tracking.CardSetRecord.T_SONG:
            return (aset.max_date(), 5)
        elif aset.set_type == card_tracking.CardSetRecord.T_FES:
            return (aset.max_date(), 9)
        elif aset.set_type == card_tracking.CardSetRecord.T_PARTY:
            return (aset.max_date(), 8)
        elif aset.set_type == card_tracking.CardSetRecord.T_PICKUP:
            return (aset.max_date(), 7)
        return (aset.max_date(), -9999)

    def get_same_group_for_all_members(self, aset: card_tracking.CardSetRecord) -> Optional[int]:
        if not aset.card_refs:
            return None

        match = aset.card_refs[0].card.member.group
        for c in aset.card_refs:
            if c.card.member.group != match:
                return None

        return match

    def get_skip_member_list(self, aset: card_tracking.CardSetRecord) -> List[int]:
        if not (grp := self.get_same_group_for_all_members(aset)):
            return []

        if grp == 3:
            if aset.nijigasaki_member_state == 0:
                return [210, 211, 212]
            elif aset.nijigasaki_member_state == 1:
                return [211, 212]
            else:
                return []

        return []

    def should_fill(self, aset: card_tracking.CardSetRecord):
        return (
            (self.get_same_group_for_all_members(aset) is not None)
            and aset.set_type in self.FILL_SET_TYPES
            and len(aset.card_refs) > self.ALL_MEMBER_SET_THRES
        )

    def matrix_order(
        self, aset: card_tracking.CardSetRecord
    ) -> Iterable[Tuple[Member, Optional[Card]]]:
        crefs_by_member = {x.card.member.id: x for x in aset.card_refs}

        if self.should_fill(aset):
            the_group = aset.card_refs[0].card.member.group
            skip_list = self.get_skip_member_list(aset)
            member_list = self.master().lookup_member_list(group=the_group)
            for member in member_list:
                card = crefs_by_member.get(member.id)
                if member.id in skip_list and card is None:
                    continue
                yield (member, card)

            # leftovers?
            # if crefs_by_member:
            #    for card in crefs_by_member.values():
            #        yield (card.member, card)
        else:
            for cid in sorted(aset.card_refs, key=lambda x: x.card.rarity, reverse=True):
                yield (cid.card.member, cid)

    def url_for_page(self, pageno: int):
        args = []
        _tag = self.get_argument("use_dates", None)
        tag = self.database().news_database.validate_server_id(_tag)

        if tag == _tag:
            args.append(f"use_dates={tag}")

        cat = self.get_argument("type", None)
        if cat in self.VALID_CATEGORIES:
            args.append(f"type={cat}")

        if pageno > 1:
            page_frag = f"{pageno}/"
        else:
            page_frag = ""

        qs = ("?" + "&".join(args)) if args else ""
        return f"/cards/sets/{page_frag}{qs}"

    async def get(self, page=None):
        try:
            pageno = max(int(page) - 1, 0)
        except TypeError:
            pageno = 0

        raw_tag = self.get_argument("use_dates", None)
        if not raw_tag:
            raw_tag = self.get_cookie("dsid", None)
        tag = self.database().news_database.validate_server_id(raw_tag)

        _cat = self.get_argument("type", None)
        cat = self.VALID_CATEGORIES.get(_cat, None)

        sets = await self.database().card_tracker.get_card_sets(
            page=pageno,
            n_entries=8,
            tag=tag,
            category=cat,
        )
        count = await self.database().card_tracker.get_card_set_count(tag=tag, category=cat)
        sets.sort(key=self.custom_sort_key, reverse=True)
        self.resolve_cards(sets)

        new_tl, new_alt = self.settings["string_access"].lookup_strings(
            self.tl_batch, self.get_user_dict_preference()
        )
        self._tlinject_base[0].update(new_tl)
        self._tlinject_base[1].update(new_alt)
        self.render(
            "card_sets.html",
            sets=sets,
            current_page=pageno + 1,
            page_count=int((count / 8) + 1),
            server_id=tag,
            prefilled_form={
                "category": _cat if cat is not None else None,
                "use_dates": tag if tag == raw_tag else None,
            },
        )

    @staticmethod
    def make_synthetic_name(handler: RequestHandler, rep: str):
        m = re.match(r"synthetic.cat([0-9]+).g([0-9]+).ord([0-9]+)", rep)
        if not m:
            return

        part_src = handler.settings["static_strings"].get(handler.locale.code, "en")

        sub_type = int(m.group(1))
        if sub_type == 2:
            gacha_type = part_src.gettext("kars.gallery.fragment.gacha_type_pickup")
        elif sub_type == 3:
            gacha_type = part_src.gettext("kars.gallery.fragment.gacha_type_fes")
        else:
            gacha_type = part_src.gettext("kars.gallery.fragment.gacha_type_party")

        group = int(m.group(2))
        if group == 1:
            school = part_src.gettext("k.m_dic_group_name_muse")
        elif group == 2:
            school = part_src.gettext("k.m_dic_group_name_aqours")
        else:
            school = part_src.gettext("k.m_dic_group_name_niji")

        fmt_string = handler.locale.translate("SetRecord.{school}{gacha_type}URsRound{set_num}")
        set_num = int(m.group(3)) + 1
        return fmt_string.format(school=school, gacha_type=gacha_type, set_num=set_num)

    def resolve_cards(self, items: Iterable[card_tracking.CardSetRecord]):
        for item in items:
            cards = self.settings["master"].lookup_multiple_cards_by_id(
                list(x.id for x in item.card_refs)
            )
            for card, ref in zip(cards, item.card_refs):
                ref.card = card

            for card in cards:
                self.tl_batch.update(card.get_tl_set())
            if item.is_systematic():
                self._tlinject_base[0][item.representative] = CardGallery.make_synthetic_name(
                    self, item.representative
                )


@route(r"/cards/set/([^/]+)")
class CardGallerySingle(CardGallery):
    async def get(self, slug):
        raw_tag = self.get_argument("use_dates", None)
        if not raw_tag:
            raw_tag = self.get_cookie("dsid", None)
        tag = self.database().news_database.validate_server_id(raw_tag)

        the_set = await self.database().card_tracker.get_single_card_set(slug)
        if not the_set:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return

        self.resolve_cards((the_set,))

        new_tl, new_alt = self.settings["string_access"].lookup_strings(
            self.tl_batch, self.get_user_dict_preference()
        )
        self._tlinject_base[0].update(new_tl)
        self._tlinject_base[1].update(new_alt)

        view_tag = self.get_argument("view_type", None)
        if view_tag != "compact":
            view_tag = "full"

        self.render(
            "card_set_single.html",
            set=the_set,
            server_id=tag,
            view_type=view_tag,
            title=self._tlinject_base[0].get(the_set.representative),
        )


# ----- AJAX (SEARCH) --------------------------------


@route(r"/api/private/cards/ajax/([0-9,]+)")
class CardPageAjax(BaseHTMLHandler, DatabaseMixin, CardThumbnailProviderMixin):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        CardThumbnailProviderMixin.initialize(self)

    def get(self, ids):
        ids = card_spec(ids)

        cards = self.settings["master"].lookup_multiple_cards_by_id(ids)
        cards = [c for c in cards if c]

        tlbatch = set()
        for card in cards:
            if card:
                tlbatch.update(card.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        if len(cards) == 0:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return

        self.render("cards_ajax.html", cards=cards)


# ----- API ------------------------------------------


@route(r"/api/private/cards/id_list\.json")
class CardListAPI(RequestHandler):
    def get(self):
        ordinals = self.settings["master"].all_ordinals()
        ids = self.settings["master"].card_ordinals_to_ids(ordinals)

        self.write({"result": [{"ordinal": ord, "id": id} for ord, id, in zip(ordinals, ids)]})


class CardAPIExtras(object):
    def init_api_extra_mixin(self):
        self.image_urls = {}
        self.translations = {}
        self.skill_fmts = {}
        self.skill_targets = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if RequestHandler not in cls.__mro__:
            raise TypeError("This mixin needs to be used with a subclass of RequestHandler.")

    def prepare_for_export(self, cards):
        handler = cast(RequestHandler, self)
        describer = get_skill_describer(handler)
        skill_target_base = handler.settings["static_strings"].get(handler.locale.code, "en")
        tlbatch = set()
        f_args = None

        for card in cards:
            ext = "jpg" if card.rarity >= 20 else "png"
            if na := card.normal_appearance:
                self.image_urls[na.image_asset_path] = image_url_reify(
                    self, na.image_asset_path, ext=ext
                )
                self.image_urls[na.thumbnail_asset_path] = card_icon_url(self, card, na, ext="png")
            if ia := card.idolized_appearance:
                self.image_urls[ia.image_asset_path] = image_url_reify(
                    self, ia.image_asset_path, ext=ext
                )
                self.image_urls[ia.thumbnail_asset_path] = card_icon_url(self, card, ia, ext="png")

            tlbatch.update(card.get_tl_set())

            if skill := card.active_skill:
                self.skill_fmts[skill.id] = describer.format_effect(
                    skill, format_args=f_args, format_args_sec=f_args
                )
                self.skill_targets[(card.id, skill.id)] = describer.format_target(
                    skill, skill_target_base, context=card
                )

            for passive in card.passive_skills:
                self.skill_fmts[passive.id] = describer.format_effect(
                    passive, format_args=f_args, format_args_sec=f_args
                )
                self.skill_targets[(card.id, passive.id)] = describer.format_target(
                    passive, skill_target_base, context=card
                )

        dict_pref = self.get_user_dict_preference()
        sd = handler.settings["string_access"].lookup_strings(tlbatch, dict_pref)
        self.translations = sd[0]

    def modify(self, cdict: Dict[str, Any], with_index_data: Dict[str, Dict[str, Any]]):
        if appearance := cdict["normal_appearance"]:
            appearance["name"] = self.translations.get(appearance["name"])
            appearance["image_asset_path"] = self.image_urls.get(appearance["image_asset_path"])
            appearance["thumbnail_asset_path"] = self.image_urls.get(
                appearance["thumbnail_asset_path"]
            )

        if appearance := cdict["idolized_appearance"]:
            appearance["name"] = self.translations.get(appearance["name"])
            appearance["image_asset_path"] = self.image_urls.get(appearance["image_asset_path"])
            appearance["thumbnail_asset_path"] = self.image_urls.get(
                appearance["thumbnail_asset_path"]
            )

        if skill := cdict["active_skill"]:
            skill["name"] = self.translations.get(skill["name"])
            skill["description"] = self.translations.get(skill["description"])
            skill["programmatic_description"] = self.skill_fmts.get(skill["id"])
            skill["programmatic_target"] = self.skill_targets.get((cdict["id"], skill["id"]))

        for passive in cdict["passive_skills"]:
            passive["name"] = self.translations.get(passive["name"])
            passive["description"] = self.translations.get(passive["description"])
            passive["programmatic_description"] = self.skill_fmts.get(passive["id"])
            passive["programmatic_target"] = self.skill_targets.get((cdict["id"], passive["id"]))

        if db_ent := with_index_data.get(cdict["id"]):
            source_id = db_ent.get("source")
            # XXX: hack: this is e_gacha_p2, which will eventually be removed
            #      for now, map it to e_gacha
            if source_id == 4:
                source_id = 3
            cdict["source"] = source_id

            cdict["release_dates"] = {
                k: v.astimezone(timezone.utc).isoformat() if v else v
                for k, v in db_ent.get("release_dates", {}).items()
            }

        return cdict


@route(r"/api/private/cards/(id|ordinal)/([0-9,]+)\.json")
class CardPageAPI(BaseAPIHandler, DatabaseMixin, CardAPIExtras):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.init_api_extra_mixin()

    async def get_index_data(self, for_ids: List[int]):
        query = {
            "id": {"value": for_ids, "return": True},
            "source": {"return": True},
            "release_dates.server_id": {"return": True},
            "release_dates.date": {"return": True},
        }

        expert = db_expert.PostgresDBExpert(CardIndex)
        async with self.database().pool.acquire() as connection, connection.transaction():
            await connection.execute("SET TRANSACTION READ ONLY")
            search_result = await expert.run_query(connection, query, order_by="id")

        ret = {}
        for row in search_result:
            if row["id"] not in ret:
                ret[row["id"]] = {
                    "source": row["source"],
                    "release_dates": {row["server_id"]: row["date"]},
                }
            else:
                ret[row["id"]]["release_dates"][row["server_id"]] = row["date"]

        return ret

    async def get(self, mode, spec):
        id_list = card_spec(spec)

        if mode == "ordinal":
            id_list = self.settings["master"].card_ordinals_to_ids(id_list)

        index_data = await self.get_index_data(id_list)
        cards = self.settings["master"].lookup_multiple_cards_by_id(id_list)
        cards = [c for c in cards if c]

        if cards:
            self.prepare_for_export(cards)
            cards = [self.modify(c.to_dict(), index_data) for c in cards]
            self.write({"result": cards})
        else:
            self.set_status(404)
            self.write({"error": "No results."})


@route(r"/api/private/cards/member/([0-9]+)\.json")
class CardPageAPIByMemberID(CardPageAPI, CardAPIExtras):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        self.init_api_extra_mixin()

    async def get(self, member_id):
        member = self.settings["master"].lookup_member_by_id(member_id)

        if not member:
            self.set_status(404)
            self.write({"error": "No results."})
            return

        card_ids = [cl.id for cl in reversed(member.card_brief)]
        index_data = await self.get_index_data(card_ids)
        cards = self.settings["master"].lookup_multiple_cards_by_id(card_ids)
        cards = [c for c in cards if c]

        if cards:
            self.prepare_for_export(cards)
            cards = [self.modify(c.to_dict(), index_data) for c in cards]
            self.write({"result": cards})
        else:
            self.set_status(404)
            self.write({"error": "No results."})
