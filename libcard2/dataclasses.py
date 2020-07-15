import struct
from collections import namedtuple
from dataclasses import dataclass, field
from typing import List, Tuple
from weakref import ref

from dataclasses_json import dataclass_json, config as JSONConfig

from .skill_cs_enums import TT
from .utils import get_coding_context


def _load_tl(string):
    return get_coding_context().get(string, string)


@dataclass_json
@dataclass
class Member(object):
    id: int
    group: int
    subunit: int
    year: int
    name: str = field(metadata=JSONConfig(encoder=_load_tl))
    name_romaji: str = field(metadata=JSONConfig(encoder=_load_tl))
    birth_month: int
    birth_day: int
    theme_color: int

    group_name: str = field(metadata=JSONConfig(encoder=_load_tl))
    subunit_name: str = field(metadata=JSONConfig(encoder=_load_tl))

    thumbnail_image_asset_path: str
    standing_image_asset_path: str
    signature_asset_path: str
    member_icon_asset_path: str

    card_brief: List = field(default_factory=list)

    def css_color(self):
        if self.theme_color < 0:
            self.theme_color = struct.unpack("<I", struct.pack("<i", self.theme_color))[0]

        return "#{0:0>6}".format(hex((self.theme_color >> 8) & 0xFFFFFF)[2:])

    def ascii_name(self):
        return ""

    def get_tl_set(self):
        return {
            self.name,
            self.name_romaji,
            self.subunit_name,
            self.group_name,
        }


@dataclass_json
@dataclass
class Skill(object):
    @dataclass
    class TargetType(object):
        id: int
        self_only: bool
        not_self: bool
        apply_count: int

        owner_party: bool
        owner_school: bool
        owner_year: bool
        owner_subunit: bool
        owner_attribute: bool
        owner_role: bool

        fixed_attributes: List[int] = field(default_factory=list)
        fixed_members: List[int] = field(default_factory=list)
        fixed_subunits: List[int] = field(default_factory=list)
        fixed_schools: List[int] = field(default_factory=list)
        fixed_years: List[int] = field(default_factory=list)
        fixed_roles: List[int] = field(default_factory=list)

        def is_all_but(self):
            return (self.fixed_attributes and len(self.fixed_attributes) >= 4) or (
                self.fixed_roles and len(self.fixed_roles) > 3
            )

    @dataclass
    class Condition(object):
        condition_type: int
        condition_value: int

    Effect = namedtuple(
        "Effect",
        (
            "target_parameter",
            "effect_type",
            "effect_value",
            "scale_type",
            "calc_type",
            "timing",
            "finish_type",
            "finish_value",
        ),
    )

    id: int
    name: str = field(metadata=JSONConfig(encoder=_load_tl))
    description: str = field(metadata=JSONConfig(encoder=_load_tl))

    skill_type: int
    sp_gauge_point: int
    icon_asset_path: str
    thumbnail_asset_path: str
    rarity: int

    trigger_type: int
    trigger_probability: int

    target: TargetType
    conditions: List[Condition] = field(default_factory=list)
    levels: List[Effect] = field(default_factory=list)
    levels_2: List[Effect] = None

    def has_complex_trigger(self):
        return self.trigger_type != TT.Non

    def get_tl_set(self):
        a = {self.name, self.description}
        return a


@dataclass_json
@dataclass
class Card(object):
    CostumeInfo = namedtuple("CostumeInfo", ("thumbnail", "costume_id", "name", "variants"))
    LevelValues = namedtuple("LevelValues", ("level", "appeal", "stamina", "technique"))

    @dataclass
    class Appearance(object):
        name: str = field(metadata=JSONConfig(encoder=_load_tl))
        image_asset_path: str
        thumbnail_asset_path: str

    @dataclass
    class RoleEffect(object):
        change_effect_type: int
        change_effect_value: int
        positive_type: int
        positive_value: int
        negative_type: int
        negative_value: int

    id: int
    ordinal: int
    rarity: int
    max_level: int
    attribute: int
    role: int
    training_tree_m_id: int
    sp_point: int
    exchange_item_id: int
    max_passive_skill_slot: int
    background_asset_path: str

    member: Member = field(metadata=JSONConfig(encoder=lambda member: member["id"]))
    role_effect: RoleEffect
    normal_appearance: Appearance
    idolized_appearance: Appearance

    active_skill: Skill
    passive_skills: List[Skill]
    idolized_offset: LevelValues
    tt_offset: LevelValues

    stats: List[LevelValues] = None
    costume_info: CostumeInfo = None

    def get_tl_set(self):
        se = {self.normal_appearance.name, self.idolized_appearance.name} | self.member.get_tl_set()
        if self.active_skill:
            se |= self.active_skill.get_tl_set()
        if self.passive_skills:
            for p in self.passive_skills:
                se.update(p.get_tl_set())
        return se


@dataclass
class CardLite(object):
    id: int
    ordinal: int
    rarity: int
    attribute: int
    role: int
    normal_appearance: Card.Appearance
    idolized_appearance: Card.Appearance


# -*- LIVEs -*-


@dataclass
class LiveWaveMission(object):
    wave_num: int
    name: str
    description: str

    origin_lang: dict

    @dataclass
    class Gimmick(Skill):
        wave_state: int = None

        def requires_temporal_descriptor(self):
            return 2 <= self.wave_state <= 4

    gimmick: Gimmick = None


@dataclass
class LiveDifficulty(object):
    id: int
    level: int

    s_score: int
    a_score: int
    b_score: int
    c_score: int

    expect_show_power: int
    expect_stamina: int
    sp_gauge_size: int
    note_damage: int
    note_score_cap: int

    stage_gimmicks: List[Skill] = None
    note_gimmicks: List[Skill] = None
    wave_missions: List[LiveWaveMission] = None

    def get_tl_set(self):
        s = set()
        for g in self.stage_gimmicks:
            s |= g.get_tl_set()
        for g in self.note_gimmicks:
            s |= g.get_tl_set()
        for g in self.wave_missions:
            s.add(g.name)
            s.add(g.description)
        return s


@dataclass
class Live(object):
    id: int
    name: str
    member_group: int
    member_unit: int
    cover_asset_path: str
    member_group_name: str
    member_unit_name: str
    order: int

    difficulties: List[LiveDifficulty] = None

    def get_tl_set(self):
        s = {self.name, self.member_group_name, self.member_unit_name}
        if self.difficulties:
            for diff in self.difficulties:
                s |= diff.get_tl_set()
        return s
