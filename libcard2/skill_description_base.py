from .dataclasses import Skill, Card
from .string_mgr import DictionaryAccess
from typing import Callable, Union, Optional
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

        if eff_d_type > 1:
            vf = vs.effect_value / 100
            vi = vs.effect_value // 100

            if vf == vi:
                vf = vi

            return f"{vf}%"
        return str(vs.effect_value)

    def default_birdseye(self, effect1, effect2=None):
        return ""

    def default_finish(self, skill: Skill.Effect):
        return ""

    def default_trigger(self, skill: Skill):
        return ""

    def default_target(self, tt: Skill.TargetType, strings: DictionaryAccess, context: Card):
        return ""

    def default_combiner(self, trigger: str, effect: str):
        return " ".join([trigger, effect])

    def finish_clause(self, f: Callable[[Skill.Effect, dict], str]):
        self.finish = f
        return f

    def birdseye_clause(self, f: Callable[[tuple, Optional[tuple]], str]):
        self.birdseye = f
        return f

    def trigger_clause(self, f: Callable[[Skill, dict], str]):
        self.trigger = f
        return f

    def target_clause(self, f: Callable[[Skill.TargetType, Card], str]):
        self.target = f
        return f

    def final_combiner(self, f: Callable[[str, str], str]):
        self.combiner = f
        return f

    def format_single_value(self, level_struct):
        return self.mod_value(level_struct)

    def format_target(
        self,
        tt: Skill,
        strings: DictionaryAccess,
        context: Card = None,
        format_args: dict = None,
        format_args_sec: dict = None
    ):
        if format_args is None:
            format_args = {"var": "", "let": "", "end": ""}
        if format_args_sec is None:
            format_args_sec = format_args

        e1 = None
        e2 = None

        if tt.levels[0].effect_type not in IMPLICIT_TARGET_SKILL_TYPES:
            e1 = self.target(tt.target, strings, context)
        if (tt.levels_2 and tt.levels_2[0].effect_type not in IMPLICIT_TARGET_SKILL_TYPES 
            and tt.target_2 and tt.target_2.id != tt.target.id):
            e2 = self.target(tt.target_2, strings, context)

        if e1 and e2:
            return self.display_dual_effect(e1, e2, format_args=format_args, format_args_sec=format_args_sec)
        elif e1:
            return e1
        elif e2:
            return e2

        return ""

    def find_formatter(self, effect_type):
        desc = self.skill_effect.get(effect_type)
        if not desc:
            return None

        if callable(desc):
            return desc

        return desc.format

    def display_value(self, levels, at_level):
        if at_level is not None:
            value = self.birdseye(levels[at_level])
        else:
            value = self.birdseye(levels[0], levels[-1])
        return value

    def display_dual_effect(
        self, 
        effect_1: str, 
        effect_2: str,
        format_args: dict,
        format_args_sec: dict
    ):
        return (
            f"{format_args['let']}①{format_args['end']}&nbsp;{effect_1} "
            f"{format_args_sec['let']}②{format_args_sec['end']}&nbsp;{effect_2}"
        )

    def format_effect(
        self,
        skill: Skill,
        level: int = None,
        format_args: dict = None,
        format_args_sec: dict = None,
    ):
        if format_args is None:
            format_args = {"var": "", "let": "", "end": ""}
        if format_args_sec is None:
            format_args_sec = format_args

        formatter = self.find_formatter(skill.levels[0].effect_type)

        if skill.levels_2:
            formatter_sec = self.find_formatter(skill.levels_2[0].effect_type)
        else:
            formatter_sec = None

        if formatter is None or (skill.levels_2 and formatter_sec is None):
            return None

        if len(skill.levels) == 1:
            level = 0

        value = self.display_value(skill.levels, level)
        trigger = self.trigger(skill, format_args)
        effect = " ".join(
            (formatter(value=value, **format_args), self.finish(skill.levels[0], format_args))
        )

        if skill.levels_2:
            value_2 = self.display_value(skill.levels_2, level)
            effect_2 = " ".join(
                (
                    formatter_sec(value=value_2, **format_args_sec),
                    self.finish(skill.levels_2[0], format_args_sec),
                )
            )
            effect = self.display_dual_effect(effect, effect_2, format_args, format_args_sec)

        return self.combiner(trigger, effect)
