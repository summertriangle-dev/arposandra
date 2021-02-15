import json
import logging
import zlib
from binascii import hexlify
from dataclasses import dataclass, field

from libcard2.dataclasses import Card as libcard2_card, Skill as libcard2_skill
from libcard2 import skill_cs_enums
from maintenance.mtrack.newsminer import AnySRecord, SEventRecord, SGachaMergeRecord

from .indexer.types import Field, Schema


@dataclass
class CardExpert(object):
    ROLES = {
        1: "voltage",
        2: "sp",
        3: "guard",
        4: "skill",
    }
    ATTRIBUTES = {
        1: "smile",
        2: "pure",
        3: "cool",
        4: "active",
        5: "natural",
        6: "elegant",
    }
    SOURCES = {1: "initial", 2: "fes_gacha", 3: "event_gacha", 4: "event", 5: "promo"}
    card: libcard2_card

    def id(self):
        return self.card.id

    def ordinal(self):
        return self.card.ordinal

    def rarity(self):
        return self.card.rarity

    def member(self):
        return self.card.member.id

    def member_group(self):
        return self.card.member.group

    def member_subunit(self):
        return self.card.member.subunit

    def member_year(self):
        return self.card.member.year

    def max_appeal(self):
        c = self.card
        return c.stats[c.max_level - 1].appeal + c.idolized_offset.appeal + c.tt_offset[-1].appeal

    def max_stamina(self):
        c = self.card
        return (
            c.stats[c.max_level - 1].stamina + c.idolized_offset.stamina + c.tt_offset[-1].stamina
        )

    def max_technique(self):
        c = self.card
        return (
            c.stats[c.max_level - 1].technique
            + c.idolized_offset.technique
            + c.tt_offset[-1].technique
        )

    def role(self):
        return self.ROLES.get(self.card.role)

    def attribute(self):
        return self.ATTRIBUTES.get(self.card.attribute)

    def skills(self):
        if self.card.active_skill:
            yield (
                self.card.active_skill.levels[0].effect_type,
                0xFFFF,
                self._to_skill_apply_type(
                    self.card.active_skill.levels[0].effect_type, self.card.active_skill.target
                ),
            )
            if self.card.active_skill.levels_2:
                yield (
                    self.card.active_skill.levels_2[0].effect_type,
                    0xFFFF,
                    self._to_skill_apply_type(
                        self.card.active_skill.levels_2[0].effect_type,
                        self.card.active_skill.target_2,
                    ),
                )

        for skill in self.card.passive_skills:
            yield (
                skill.levels[0].effect_type,
                skill.trigger_type,
                self._to_skill_apply_type(skill.levels[0].effect_type, skill.target),
            )
            if skill.levels_2:
                yield (
                    skill.levels_2[0].effect_type,
                    skill.trigger_type,
                    self._to_skill_apply_type(skill.levels_2[0].effect_type, skill.target_2),
                )

    def _to_skill_apply_type(self, eff, tt: libcard2_skill.TargetType):
        if eff in skill_cs_enums.IMPLICIT_TARGET_SKILL_TYPES:
            return "none"

        if tt.self_only:
            return "self"
        elif tt.owner_party:
            return "party"
        elif tt.owner_school:
            return "group"
        elif tt.owner_year:
            return "year"
        elif tt.owner_subunit:
            return "subunit"
        elif tt.owner_attribute:
            return "attribute"
        elif tt.owner_role:
            return "role"
        elif tt.fixed_members and tt.fixed_members[0] == self.card.member.id:
            return "member"
        elif tt.apply_count >= 8 and tt.not_self:
            return "everyone_not_self"
        elif tt.apply_count >= 8:
            return "everyone"
        else:
            return "special"

        return "none"

    def maximal_stat(self):
        return max(
            (
                (self.max_appeal(), "appeal"),
                (self.max_stamina(), "stamina"),
                (self.max_technique(), "technique"),
            )
        )[1]

    def source(self):
        return Schema.Empty

    def release_dates(self):
        return Schema.Empty


CardIndex = Schema(
    "card_index_v1",
    fields=[
        Field.integer(
            "id", primary=True, behaviour={"digits": "9", "compare_type": "equal", "sort": False}
        ),
        Field.integer("ordinal"),
        Field.integer(
            "member",
            behaviour={"captain_treat_as": "enum", "conflicts": ["member_group", "member_subunit"], "grouped": True},
        ),
        Field.integer(
            "member_group",
            behaviour={
                "captain_treat_as": "enum",
                "sort": False,
                "conflicts": ["member", "member_subunit"],
            },
        ),
        Field.integer(
            "member_subunit",
            behaviour={
                "captain_treat_as": "enum",
                "sort": False,
                "conflicts": ["member", "member_group"],
                "grouped": True
            },
        ),
        Field.integer("member_year", behaviour={"captain_treat_as": "enum", "sort": False}),
        Field.integer("max_appeal"),
        Field.integer("max_stamina"),
        Field.integer("max_technique"),
        Field.integer(
            "rarity",
            behaviour={"captain_treat_as": "enum", "compare_type": "bit-set", "sort": "numeric"},
        ),
        Field.enum(
            "source",
            ("unspec", "event", "e_gacha", "e_gacha_p2", "pickup", "fes", "party"),
            behaviour={"captain_treat_as": "enum", "compare_type": "bit-set", "sort": False},
        ),
        Field.enum(
            "role",
            ("voltage", "sp", "guard", "skill"),
            behaviour={"compare_type": "bit-set", "icons": "/static/images/search/role"},
        ),
        Field.enum(
            "attribute",
            ("smile", "pure", "cool", "active", "natural", "elegant"),
            behaviour={"compare_type": "bit-set", "icons": "/static/images/search/attribute"},
        ),
        Field.enum("maximal_stat", ("appeal", "stamina", "technique"), behaviour={"sort": False}),
        Field.composite(
            "skills",
            Field.integer("effect", behaviour={"captain_treat_as": "enum", "sort": False}),
            Field.integer("activation_type", behaviour={"captain_treat_as": "enum", "sort": False}),
            Field.enum(
                "apply_type",
                (
                    "self",
                    "party",
                    "member",
                    "role",
                    "attribute",
                    "subunit",
                    "group",
                    "year",
                    "everyone_not_self",
                    "everyone",
                    "special",
                    "none",
                ),
                behaviour={"sort": False},
            ),
            multiple=True,
        ),
        Field.composite(
            "release_dates", Field.varchar("server_id", 8, primary=True), Field.datetime("date"),
        ),
    ],
    expert=CardExpert,
)


@dataclass
class SetRecord(object):
    name: str
    representative_name: str
    stype: str = "same_name"
    members: list = field(default_factory=list)

    def __post_init__(self):
        self.current_prio = None

    def replace_representative(self, repl, prio):
        if not self.current_prio or prio < self.current_prio:
            self.current_prio = prio
            self.representative_name = repl

    # This class is its own expert
    def id(self):
        try:
            ascii_name = self.name.encode("ascii")
            ascii_name = self.name
        except UnicodeEncodeError:
            hash = zlib.crc32(self.name.encode("utf8")).to_bytes(4, "big")
            ascii_name = "set-" + hexlify(hash).decode("ascii")

        return ascii_name.lower().replace(" ", "-").replace("/", "-")

    def representative(self):
        return self.representative_name

    def card_ids(self):
        return self.members

    def set_type(self):
        return self.stype

    def sort_dates(self):
        return Schema.Empty

    def shioriko_exists(self):
        if self.stype in ["ordinal_fes", "ordinal_pickup"]:
            return 1
        return Schema.Empty


SetIndex = Schema(
    "card_p_set_index_v1",
    fields=[
        Field.text("id"),
        Field.text("representative", primary=True),
        Field.enum(
            "set_type",
            ("same_name", "event", "song", "ordinal_fes", "ordinal_pickup", "initial", "else"),
        ),
        Field.integer("shioriko_exists"),
        Field.composite(
            "sort_dates", Field.varchar("server_id", 8, primary=True), Field.datetime("date")
        ),
        Field.integer("card_ids", multiple=True),
    ],
    expert=lambda x: x,
)


class SRecordExpert(object):
    def __init__(self, srecord: AnySRecord):
        self.record = srecord

    def id(self):
        return self.record.record_id

    def serverid(self):
        return self.record.server_id

    def what(self):
        if isinstance(self.record, SGachaMergeRecord):
            return 1
        else:
            return 2

    def title(self):
        return self.record.common_title

    def card_ids(self):
        if isinstance(self.record, SGachaMergeRecord):
            return self.record.feature_card_ids.items()
        else:
            return ((x, "event") for x in self.record.feature_card_ids)

    def subtype(self):
        if isinstance(self.record, SGachaMergeRecord):
            return self.record.maybe_type
        else:
            return Schema.Empty

    def thumbnail(self):
        return self.record.thumbnail or Schema.Empty

    def sort_date(self):
        if isinstance(self.record, SGachaMergeRecord):
            return self.record.time_spans["gacha"][0]
        else:
            return self.record.time_span[0]

    def dates(self):
        if isinstance(self.record, SGachaMergeRecord):
            ts = self.record.time_spans["gacha"]
            yield ("gacha_start", ts[0], None)
            yield ("gacha_end", ts[0] + ts[1], None)
            ts = self.record.time_spans.get("event")
            if ts:
                yield ("event_start", ts[0], None)
                yield ("event_end", ts[0] + ts[1], None)
            ts = self.record.time_spans.get("part2")
            if ts:
                yield ("gachap2_start", ts[0], None)
                yield ("gachap2_end", ts[0] + ts[1], None)
        else:
            ts = self.record.time_span
            yield ("event_start", ts[0], None)
            yield ("event_end", ts[0] + ts[1], None)


HistoryIndex = Schema(
    "history_v5",
    fields=[
        Field.integer("id", primary=True),
        Field.varchar("serverid", 8, primary=True),
        Field.integer("what"),
        Field.text("title"),
        Field.integer("subtype"),
        Field.varchar("thumbnail", 8),
        Field.datetime("sort_date"),
        Field.composite(
            "dates",
            Field.enum(
                "type",
                (
                    "event_start",
                    "gacha_start",
                    "gachap2_start",
                    "event_end",
                    "gacha_end",
                    "gachap2_end",
                    "ig_event_id",
                ),
                primary=True,
            ),
            Field.datetime("date"),
            Field.integer("value"),
        ),
        Field.composite(
            "card_ids",
            Field.integer("card_id", primary=True),
            Field.enum("what", ("unspec", "event", "e_gacha", "e_gacha_p2", "pickup", "fes", "party")),
        ),
    ],
    expert=SRecordExpert,
)
