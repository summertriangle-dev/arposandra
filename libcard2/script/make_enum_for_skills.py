import re
import json

import plac

from libcard2 import skill_cs_enums
from libcard2.localization.skills_en import EN


def make_systematic_name(name):
    """
    Something like AddAppealBaseBonusChangingHpRateMax ->
        Add appeal base bonus changing hp rate max .
    Word soup for most enumerated skill names but is a good starting point
    """
    return " ".join(re.findall(r"([A-Z]+[a-z]*)", name)).capitalize()


def build_choices(string_src, clz, test, _=None):
    choices = []
    for name in (name for name in clz.__dict__ if not name.startswith("_")):
        if not test(name):
            continue

        prev_name = string_src.get(getattr(clz, name))
        if not prev_name:
            systematic_name = make_systematic_name(name)

        choices.append(
            {
                "name": name,
                "display_name": EN.skill_effect.get(getattr(clz, name))
                if _
                else (prev_name or systematic_name),
                "value": getattr(clz, name),
            }
        )

    return {"choices": choices}


def to_table(choice_list):
    return {c["value"]: c["display_name"] for c in choice_list}


@plac.pos("output_file", "Where to write the definitions.")
def main(output_file):
    prev = {}
    try:
        with open(output_file, "r") as injs:
            prev = json.load(injs).get("criteria", {})
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    table = {
        "criteria": {
            "skills.effect": build_choices(
                to_table(prev.get("skills.effect", {}).get("choices", {})),
                skill_cs_enums.ST,
                lambda x: getattr(skill_cs_enums.ST, x) in EN.skill_effect,
                True,
            ),
            "skills.activation_type": build_choices(
                to_table(prev.get("skills.activation_type", {}).get("choices", {})),
                skill_cs_enums.TT,
                lambda _: True,
            ),
        }
    }

    with open(output_file, "w") as outjs:
        json.dump(table, outjs, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    plac.call(main)
