from .dataclasses import Skill, Card
from .string_mgr import DictionaryAccess
from typing import Callable, Union
from collections import UserDict

from .skill_cs_enums import (
    ST,
    IMPLICIT_TARGET_SKILL_TYPES,
    PERCENT_VALUE_SKILL_TYPES,
    MIXED_VALUE_SKILL_TYPES,
)

VALUE_PERCENT = 1
VALUE_MIXED = 2


class SkillEffectDSLHelper(UserDict):
    def __call__(self, skill_type_id):
        def _(describer):
            self.data[skill_type_id] = describer
            return describer

        return _


class SkillEffectDescriberContext(object):
    def __init__(self):
        self.finish = self.default_finish
        self.birdseye = self.default_birdseye
        self.trigger = self.default_trigger
        self.target = self.default_target
        self.combiner = self.default_combiner
        self.skill_effect = SkillEffectDSLHelper()

    @staticmethod
    def mod_value(vs):
        eff_d_type = 1
        if vs.effect_type in MIXED_VALUE_SKILL_TYPES:
            eff_d_type = vs.calc_type
        elif vs.effect_type in PERCENT_VALUE_SKILL_TYPES:
            eff_d_type = 2

        if eff_d_type == 2:
            vf = vs.effect_value / 100
            vi = vs.effect_value // 100
            if vf == vi:
                return f"{vi}%"
            return f"{vf}%"
        return str(vs.effect_value)

    def default_birdseye(self, effect1, effect2, mod):
        return ""

    def default_finish(self, skill: Skill):
        return ""

    def default_trigger(self, skill: Skill):
        return ""

    def default_target(self, tt: Skill.TargetType, strings: DictionaryAccess, context: Card):
        return ""

    def default_combiner(self, trigger: str, effect: str, finish: str):
        return " ".join([trigger, effect, finish])

    def finish_clause(self, f: Callable[[Skill, dict], str]):
        self.finish = f
        return f

    def birdseye_clause(self, f: Callable[[tuple, tuple], str]):
        self.birdseye = f
        return f

    def trigger_clause(self, f: Callable[[Skill, dict], str]):
        self.trigger = f
        return f

    def target_clause(self, f: Callable[[Skill.TargetType, Card], str]):
        self.target = f
        return f

    def final_combiner(self, f: Callable[[str, str, str], str]):
        self.combiner = f
        return f

    def format_single_value(self, level_struct):
        return self.mod_value(level_struct)

    def format_target(self, tt: Skill, strings: DictionaryAccess, context: Card = None):
        if tt.levels[0].effect_type in IMPLICIT_TARGET_SKILL_TYPES:
            return ""
        return self.target(tt.target, strings, context)

    def format_effect(self, skill: Skill, level: int = None, format_args: dict = None):
        if format_args is None:
            format_args = {"var": "", "let": "", "end": ""}

        desc = self.skill_effect.get(skill.levels[0].effect_type)
        if not desc:
            return None

        if len(skill.levels) == 1:
            level = 0

        if level is not None:
            value = self.mod_value(skill.levels[level])
        else:
            value = self.birdseye(skill.levels[0], skill.levels[-1])

        trigger = self.trigger(skill, format_args)
        if callable(desc):
            formatter = desc
        else:
            formatter = desc.format
        effect = formatter(value=value, **format_args)
        finish = self.finish(skill, format_args)
        return self.combiner(trigger, effect, finish)
