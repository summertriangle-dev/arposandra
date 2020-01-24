import struct
from collections import namedtuple
from dataclasses import dataclass
from typing import List
from weakref import ref


@dataclass
class Member(object):
    id: int
    group: int
    subunit: int
    year: int
    name: str
    name_romaji: str
    birth_month: int
    birth_day: int
    theme_color: int

    group_name: str
    subunit_name: str

    thumbnail_image_asset_path: str
    standing_image_asset_path: str
    signature_asset_path: str
    member_icon_asset_path: str

    card_brief: list = None

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


CardLevelValues = namedtuple("CardLevelValues", ("level", "appeal", "stamina", "technique"))

CardAppearance = namedtuple("CardAppearance", ("name", "image_asset_path", "thumbnail_asset_path"))


@dataclass
class CardRoleEffect(object):
    change_effect_type: int
    change_effect_value: int
    positive_type: int
    positive_value: int
    negative_type: int
    negative_value: int


@dataclass
class SkillTargetType(object):
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

    fixed_attributes: List[int] = None
    fixed_members: List[int] = None
    fixed_subunits: List[int] = None
    fixed_schools: List[int] = None
    fixed_years: List[int] = None
    fixed_roles: List[int] = None

    def is_all_but(self):
        return (self.fixed_attributes and len(self.fixed_attributes) >= 4) or (
            self.fixed_roles and len(self.fixed_roles) > 3
        )


@dataclass
class ActiveSkill(object):
    id: int
    name: str
    description: str
    skill_type: int
    trigger_probability: int
    sp_gauge_point: int
    icon_asset_path: str
    thumbnail_asset_path: str

    target: SkillTargetType = None
    levels: list = None

    def has_complex_trigger(self):
        return False

    def get_tl_set(self):
        a = {self.name, self.description}
        return a


@dataclass
class PassiveSkill(object):
    id: int
    name: str
    description: str
    rarity: int
    trigger_type: int
    trigger_probability: int
    icon_asset_path: str
    thumbnail_asset_path: str

    condition_type: int
    condition_value: int

    target: SkillTargetType = None
    levels: list = None

    def has_complex_trigger(self):
        return True

    def get_tl_set(self):
        a = {self.name, self.description}
        return a


@dataclass
class CardLite(object):
    id: int
    ordinal: int
    rarity: int
    attribute: int
    role: int
    normal_appearance: CardAppearance = None
    idolized_appearance: CardAppearance = None


@dataclass
class Card(object):
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

    member: Member = None
    role_effect: CardRoleEffect = None
    normal_appearance: CardAppearance = None
    idolized_appearance: CardAppearance = None

    active_skill: ActiveSkill = None
    passive_skills: List[PassiveSkill] = None

    stats: List[CardLevelValues] = None
    idolized_offset: CardLevelValues = None
    tt_offset: CardLevelValues = None

    def get_tl_set(self):
        se = {self.normal_appearance[0], self.idolized_appearance[0],} | self.member.get_tl_set()
        if self.active_skill:
            se |= self.active_skill.get_tl_set()
        if self.passive_skills:
            for p in self.passive_skills:
                se.update(p.get_tl_set())
        return se


# -*- -*-


@dataclass
class LiveWaveMission(object):
    wave_num: int
    name: str
    description: str

    origin_lang: dict


@dataclass
class LiveDifficulty(object):
    id: int
    level: int

    s_score: int
    a_score: int
    b_score: int
    c_score: int

    stage_gimmicks: List[ActiveSkill] = None
    note_gimmicks: List[PassiveSkill] = None
    wave_missions: List = None

    def get_tl_set(self):
        s = set()
        for g in self.stage_gimmicks:
            s |= g.get_tl_set()
        for g in self.note_gimmicks:
            s |= g.get_tl_set()
        for g in self.wave_missions:
            s.add(g.name)
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
