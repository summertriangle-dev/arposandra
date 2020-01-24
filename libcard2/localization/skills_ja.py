from ..dataclasses import Card
from ..skill_description_base import SkillEffectDescriberContext, AnySkill
from ..skill_cs_enums import ST, TT, CT, FT

JA = SkillEffectDescriberContext()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Routines for Japanese skill target descriptions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

## TODO: fill

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Routines for Japanese skill descriptions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


@JA.birdseye_clause
def _(effect1, effect2):
    m = SkillEffectDescriberContext.mod_value
    return f"{m(effect1)}〜{m(effect2)}"


# fmt: off

## TODO: Fill templates
# We're leaving this empty so the original strings are used for now.

# fmt: on
