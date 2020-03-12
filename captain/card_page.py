import random
from datetime import datetime

from tornado.web import RequestHandler

from .dispatch import route, LanguageCookieMixin
from .pageutils import tlinject_static


@route("/cards/by_idol/([0-9]+)(/.*)?")
class CardPageByMemberID(LanguageCookieMixin):
    def get(self, member_id, _):
        member = self.settings["master"].lookup_member_by_id(member_id)

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
class CardPage(LanguageCookieMixin):
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
        tlbatch = set()
        for card in cards:
            tlbatch.update(card.get_tl_set())

        self._tlinject_base = self.settings["string_access"].lookup_strings(
            tlbatch, self.get_user_dict_preference()
        )

        if len(cards) == 1:
            ct = self.locale.translate("#{card_no}: {idol_name}").format(
                idol_name=tlinject_static(self, cards[0].member.name_romaji, escape=False),
                card_no=cards[0].ordinal,
            )
        else:
            ct = self.locale.translate("{num_cards} cards").format(num_cards=len(cards))

        self.render("cards.html", cards=cards, custom_title=ct, og_context={})


@route("/cards/history")
class CardHistory(LanguageCookieMixin):
    async def get(self):
        his = await self.settings["card_tracking"].get_history_entries("jp", datetime.now(), 21)
        if len(his) == 21:
            has_more = True
        else:
            has_more = False
        self.resolve_cards(his)
        self.render("history.html", releases=his[:-1], has_next_page=has_more)

    def resolve_cards(self, items):
        for item in items:
            cards = self.settings["master"].lookup_multiple_cards_by_id(item.card_refs)
            item.card_refs = [c for c in cards if c]
