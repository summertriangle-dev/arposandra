import base64
import hashlib
import hmac
import random
import re
from datetime import datetime
from typing import Iterable, Optional, Tuple, cast

from tornado.web import RequestHandler

from libcard2.dataclasses import Card, Member
from libcard2.utils import coding_context

from .bases import BaseHTMLHandler, BaseAPIHandler
from .dispatch import DatabaseMixin, LanguageCookieMixin, route
from .models import card_tracking
from .pageutils import get_as_secret, tlinject_static
import logging


@route("/cards/by_idol/([0-9]+)(/.*)?")
class CardPageByMemberID(BaseHTMLHandler, LanguageCookieMixin):
    def get(self, member_id, _):
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

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        self.render(
            "cards.html",
            cards=cards,
            custom_title=self.locale.translate("Cards of {idol_name}").format(
                idol_name=tlinject_static(self, member.name_romaji, escape=False)
            ),
            og_context={"type": "member", "member": member},
        )


@route("/card/(random|(?:[0-9,]+))(/.*)?")
class CardPage(BaseHTMLHandler, LanguageCookieMixin):
    def card_spec(self, spec: str) -> list:
        if spec == "everything":
            return self.settings["master"].all_ordinals()

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

    def get(self, ordinal, _):
        if ordinal == "random":
            where = random.choice(self.settings["master"].all_ordinals())
            self.redirect(f"/card/{where}")
            return

        ordinals = self.card_spec(ordinal)

        cards = self.settings["master"].lookup_multiple_cards_by_id(
            self.settings["master"].card_ordinals_to_ids(ordinals)
        )
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
        elif len(cards) == 1:
            ct = self.locale.translate("#{card_no}: {idol_name}").format(
                idol_name=tlinject_static(self, cards[0].member.name_romaji, escape=False),
                card_no=cards[0].ordinal,
            )
        else:
            ct = self.locale.translate("{num_cards} cards").format(num_cards=len(cards))

        self.render("cards.html", cards=cards, custom_title=ct, og_context={})


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
class CardGallery(BaseHTMLHandler, DatabaseMixin, LanguageCookieMixin, CardThumbnailProviderMixin):
    # The largest known subunit size (QU4RTZ). This is checked so we don't treat
    # subunit costume sets as group sets.
    ALL_MEMBER_SET_THRES = 4
    FILL_SET_TYPES = [
        card_tracking.CardSetRecord.T_DEFAULT,
        card_tracking.CardSetRecord.T_SONG,
        card_tracking.CardSetRecord.T_FES,
        card_tracking.CardSetRecord.T_PICKUP,
    ]
    VALID_CATEGORIES = {
        "other": card_tracking.CardSetRecord.T_DEFAULT,
        "event": card_tracking.CardSetRecord.T_EVENT,
        "song": card_tracking.CardSetRecord.T_SONG,
        "fes": card_tracking.CardSetRecord.T_FES,
        "pickup": card_tracking.CardSetRecord.T_PICKUP,
    }
    SAME_GROUP_ORD_TYPES = [card_tracking.CardSetRecord.T_FES, card_tracking.CardSetRecord.T_PICKUP]

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
        elif aset.set_type == card_tracking.CardSetRecord.T_PICKUP:
            return (aset.max_date(), 8)
        return (aset.max_date(), -9999)

    def get_same_group_for_all_members(self, aset: card_tracking.CardSetRecord) -> Optional[int]:
        if not aset.card_refs:
            return None

        match = aset.card_refs[0].card.member.group
        for c in aset.card_refs:
            if c.card.member.group != match:
                return None

        return match

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
            skip_shioriko = not aset.shioriko_exists
            member_list = self.master().lookup_member_list(group=the_group)
            for member in member_list:
                card = crefs_by_member.get(member.id)
                if skip_shioriko and member.id == 210 and card is None:
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

    def add_synthetic_name(self, rep: str):
        m = re.match(r"synthetic.cat([0-9]+).g([0-9]+).ord([0-9]+)", rep)
        if not m:
            return

        part_src = self.settings["static_strings"].get(self.locale.code, "en")

        sub_type = int(m.group(1))
        if sub_type == 2:
            gacha_type = part_src.gettext("kars.gallery.fragment.gacha_type_pickup")
        else:
            gacha_type = part_src.gettext("kars.gallery.fragment.gacha_type_fes")

        group = int(m.group(2))
        if group == 1:
            school = part_src.gettext("k.m_dic_group_name_muse")
        elif group == 2:
            school = part_src.gettext("k.m_dic_group_name_aqours")
        else:
            school = part_src.gettext("k.m_dic_group_name_niji")

        fmt_string = self.locale.translate("SetRecord.{school}{gacha_type}URsRound{set_num}")
        set_num = int(m.group(3)) + 1
        self._tlinject_base[0][rep] = fmt_string.format(
            school=school, gacha_type=gacha_type, set_num=set_num
        )

    def resolve_cards(self, items: Iterable[card_tracking.CardSetRecord]):
        for item in items:
            cards = self.settings["master"].lookup_multiple_cards_by_id(
                list(x.id for x in item.card_refs)
            )
            for card, ref in zip(cards, item.card_refs):
                ref.card = card

            for card in cards:
                self.tl_batch.update(card.get_tl_set())
            if item.representative.startswith("synthetic."):
                self.add_synthetic_name(item.representative)


@route(r"/cards/set/([^/]+)")
class CardGallerySingle(CardGallery):
    async def get(self, slug):
        the_set = await self.database().card_tracker.get_single_card_set(slug)

        if not the_set:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return

        cards = self.settings["master"].lookup_multiple_cards_by_id(
            list(x.id for x in the_set.card_refs)
        )
        cards = [c for c in cards if c]

        if the_set.set_type in self.FILL_SET_TYPES:
            cards.sort(key=lambda x: x.member.id)
        else:
            cards.sort(key=lambda x: x.rarity, reverse=True)

        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        self.add_synthetic_name(the_set.representative)
        custom_title = "Set: {0}".format(self._tlinject_base[0].get(the_set.representative))

        if len(cards) == 0:
            self.set_status(404)
            self.render("error.html", message=self.locale.translate("ErrorMessage.ItemNotFound"))
            return

        self.render("cards.html", cards=cards, custom_title=custom_title, og_context={})


# ----- AJAX (SEARCH) --------------------------------


@route(r"/api/private/cards/ajax/([0-9,]+)")
class CardPageAjax(BaseHTMLHandler, LanguageCookieMixin, DatabaseMixin, CardThumbnailProviderMixin):
    def initialize(self, *args, **kwargs):
        super().initialize(*args, **kwargs)
        CardThumbnailProviderMixin.initialize(self)

    def card_spec(self, spec: str) -> list:
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

    def get(self, ids):
        ids = self.card_spec(ids)

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


@route(r"/api/private/cards/(id|ordinal)/([0-9,]+)\.json")
class CardPageAPI(CardPage):
    def get(self, mode, spec):
        id_list = self.card_spec(spec)

        if mode == "ordinal":
            id_list = self.settings["master"].card_ordinals_to_ids(id_list)

        cards = self.settings["master"].lookup_multiple_cards_by_id(id_list)
        cards = [c for c in cards if c]

        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        if self.get_argument("with_accept_language", False):
            dict_pref = self.get_user_dict_preference()
        else:
            dict_pref = None

        sd = self.settings["string_access"].lookup_strings(tlbatch, dict_pref)

        if cards:
            with coding_context(sd[0]):
                cards = [c.to_dict() for c in cards]
                self.write({"result": cards})
        else:
            self.set_status(404)
            self.write({"error": "No results."})


@route(r"/api/private/cards/member/([0-9]+)\.json")
class CardPageAPIByMemberID(BaseAPIHandler, LanguageCookieMixin):
    def get(self, member_id):
        member = self.settings["master"].lookup_member_by_id(member_id)

        if not member:
            self.set_status(404)
            self.write({"error": "No results."})
            return

        card_ids = [cl.id for cl in reversed(member.card_brief)]
        cards = self.settings["master"].lookup_multiple_cards_by_id(card_ids)
        cards = [c for c in cards if c]

        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        if self.get_argument("with_accept_language", False):
            dict_pref = self.get_user_dict_preference()
        else:
            dict_pref = None

        sd = self.settings["string_access"].lookup_strings(tlbatch, dict_pref)

        if cards:
            with coding_context(sd[0]):
                cards = [c.to_dict() for c in cards]
                self.write({"result": cards})
        else:
            self.set_status(404)
            self.write({"error": "No results."})
