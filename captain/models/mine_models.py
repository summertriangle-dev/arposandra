import json
import logging
from dataclasses import dataclass, field

from libcard2.dataclasses import Card as libcard2_card
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
        return c.stats[-1].appeal + c.idolized_offset.appeal + c.tt_offset[-1].appeal

    def max_stamina(self):
        c = self.card
        return c.stats[-1].stamina + c.idolized_offset.stamina + c.tt_offset[-1].stamina

    def max_technique(self):
        c = self.card
        return c.stats[-1].technique + c.idolized_offset.technique + c.tt_offset[-1].technique

    def role(self):
        return self.ROLES.get(self.card.role)

    def attribute(self):
        return self.ATTRIBUTES.get(self.card.attribute)

    def skill_major(self):
        return self.card.active_skill.levels[0].effect_type

    def skill_minors(self):
        return [skill.levels[0].effect_type for skill in self.card.passive_skills]

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

    def release_date(self):
        return Schema.Empty


CardIndex = Schema(
    "card_index_v1",
    fields=[
        Field.integer("id", primary=True),
        Field.integer("ordinal"),
        Field.integer("member"),
        Field.integer("member_group"),
        Field.integer("member_subunit"),
        Field.integer("member_year"),
        Field.integer("max_appeal"),
        Field.integer("max_stamina"),
        Field.integer("max_technique"),
        Field.integer("rarity"),
        Field.integer("source"),
        Field.datetime("release_date"),
        Field.enum("role", ("voltage", "sp", "guard", "skill")),
        Field.enum("attribute", ("smile", "pure", "cool", "active", "natural", "elegant")),
        Field.integer("skill_major"),
        Field.enum("maximal_stat", ("appeal", "stamina", "technique")),
        Field.integer("skill_minors", multiple=True),
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
        return self.name

    def representative(self):
        return self.representative_name

    def card_ids(self):
        return self.members

    def set_type(self):
        return self.stype

    def release_dates(self):
        return Schema.Empty

    def event_references(self):
        return Schema.Empty


SetIndex = Schema(
    "card_p_set_index_v1",
    fields=[
        Field.text("id"),
        Field.text("representative", primary=True),
        Field.enum("set_type", ("same_name", "event", "song", "ordinal_fes", "ordinal_pickup", "initial", "else")),
        Field.integer("card_ids", multiple=True),
        Field.composite(
            "event_references",
            Field.varchar("server_id", 8),
            Field.integer("record_id"),
            multiple=True,
        ),
        Field.composite(
            "release_dates",
            Field.varchar("server_id", 8, primary=True),
            Field.datetime("min_date"),
            Field.datetime("max_date"),
            multiple=False,
        ),
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
        return self.record.feature_card_ids

    def subtype(self):
        if isinstance(self.record, SGachaMergeRecord):
            return self.record.maybe_type
        else:
            return Schema.Empty

    def start_time(self):
        return self.record.time_span[0]

    def end_time(self):
        return self.record.time_span[0] + self.record.time_span[1]

    def internal_id(self):
        return Schema.Empty

    def thumbnail(self):
        return self.record.thumbnail or Schema.Empty


HistoryIndex = Schema(
    "history_v5",
    fields=[
        Field.integer("id", primary=True),
        Field.varchar("serverid", 8, primary=True),
        Field.integer("what"),
        Field.text("title"),
        Field.integer("subtype"),
        Field.datetime("start_time"),
        Field.datetime("end_time"),
        Field.varchar("thumbnail", 8),
        Field.integer("card_ids", multiple=True),
    ],
    expert=SRecordExpert,
)
