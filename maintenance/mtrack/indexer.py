import os
from typing import Generic, TypeVar, Callable, Any, Type, Sequence
from dataclasses import dataclass, field

from libcard2.dataclasses import Card as libcard2_card

FIELD_TYPE_INT = 1
FIELD_TYPE_STRING = 2


@dataclass
class Field(object):
    field_type: int
    name: str
    multiple: bool = False
    primary: bool = False
    map_enum_to_id: dict = field(default=None, init=False)

    @classmethod
    def enum(cls, name, choices, **kwargs):
        r = cls(FIELD_TYPE_INT, name, **kwargs)
        r.map_enum_to_id = {v: i + 1 for i, v in enumerate(choices)}
        return r

    @classmethod
    def text(cls, name, **kwargs):
        return cls(FIELD_TYPE_STRING, name, **kwargs)

    @classmethod
    def integer(cls, name, **kwargs):
        return cls(FIELD_TYPE_INT, name, **kwargs)

    def transform(self, v):
        if self.map_enum_to_id:
            return self.map_enum_to_id[v]
        return v


T = TypeVar("T")


@dataclass
class Schema(Generic[T]):
    table: str
    fields: Sequence[Field]
    expert: Callable[[T], Any]
    first_multi_index: int = field(init=False)
    primary_key: Sequence[Field] = field(init=False)

    def __post_init__(self):
        self.validate_or_error()
        try:
            self.first_multi_index = next(i for i, f in enumerate(self.fields) if f.multiple)
        except StopIteration:
            self.first_multi_index = len(self.fields)

        self.primary_key = tuple(f for f in self.fields if f.primary)

    def validate_or_error(self):
        encountered_first_multi = False
        for f in self.fields:
            if encountered_first_multi and not f.multiple:
                raise ValueError(
                    f"{self.table}: Multi-valued fields need to come after all normal fields."
                )
            if f.multiple:
                encountered_first_multi = True

    def __getitem__(self, name):
        for v in (x for x in self.fields if x.name == name):
            return v

    def sql_tuples_from_object(self, obj: T):
        expert = self.expert(obj)
        pk = getattr(expert, self.fields[0].name)()
        single = tuple(
            field.transform(getattr(expert, field.name)())
            for field in self.fields[: self.first_multi_index]
        )

        multi = []
        for field in self.fields[self.first_multi_index :]:
            multi.extend(
                (pk, field.name, field.transform(x)) for x in getattr(expert, field.name)()
            )

        return single, multi


##############################################################################


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
        fd = self.card.id // 100000000
        return self.SOURCES.get(fd)


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
        Field.enum("source", ("initial", "fes_gacha", "event_gacha", "event", "promo")),
        Field.enum("role", ("voltage", "sp", "guard", "skill")),
        Field.enum("attribute", ("smile", "pure", "cool", "active", "natural", "elegant")),
        Field.integer("skill_major"),
        Field.enum("maximal_stat", ("appeal", "stamina", "technique")),
        Field.integer("skill_minors", multiple=True),
    ],
    expert=CardExpert,
)
