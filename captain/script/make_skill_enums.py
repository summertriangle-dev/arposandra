import re
import os
import json
import asyncio

import asyncpg
import plac

from libcard2 import skill_cs_enums
from libcard2.localization.skills_en import EN

var_dict = {
    "let": "",
    "var": "",
    "end": "",
    "value": "X",
}


class DatabaseConnection(object):
    def __init__(self):
        self.connection_url = os.environ.get("AS_POSTGRES_DSN")
        self.pool = None

    async def init_models(self):
        self.pool = await asyncpg.create_pool(dsn=self.connection_url, min_size=1, max_size=1)

    async def get_skill_ids(self):
        async with self.pool.acquire() as c:
            t = await c.fetch("SELECT DISTINCT effect FROM card_index_v1__skills")
            return [x["effect"] for x in t]

    async def get_act_ids(self):
        async with self.pool.acquire() as c:
            t = await c.fetch("SELECT DISTINCT activation_type FROM card_index_v1__skills")
            return [x["activation_type"] for x in t]


def make_systematic_name(name):
    """
    Something like AddAppealBaseBonusChangingHpRateMax ->
        Add appeal base bonus changing hp rate max .
    Word soup for most enumerated skill names but is a good starting point
    """
    return " ".join(re.findall(r"([A-Z]+[a-z]*)", name)).capitalize()


def build_choices(string_src, clz, test=lambda n: True, default=make_systematic_name, debug=False):
    choices = []
    for name in (name for name in clz.__dict__ if not name.startswith("_")):
        if not test(name):
            continue

        prev_name = string_src.get(getattr(clz, name))
        if not prev_name:
            default_name = default(name)

        choices.append(
            {
                "name": name if debug else "_",
                "display_name": prev_name or default_name,
                "value": getattr(clz, name),
            }
        )

    return {"choices": choices, "type": 1000}


def to_table(choice_list):
    return {c["value"]: c["display_name"] for c in choice_list}


@plac.pos("output_file", "Where to write the definitions.")
@plac.flg("debug", "Write enum names.")
async def main(output_file, debug=False):
    prev = {}
    try:
        with open(output_file, "r") as injs:
            prev = json.load(injs).get("criteria", {})
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    dbc = DatabaseConnection()
    await dbc.init_models()
    skill_effects_in_use = await dbc.get_skill_ids()
    skill_acts_in_use = await dbc.get_act_ids()

    table = {
        "criteria": {
            "skills.effect": build_choices(
                to_table(prev.get("skills.effect", {}).get("choices", {})),
                skill_cs_enums.ST,
                lambda x: getattr(skill_cs_enums.ST, x) in skill_effects_in_use,
                default=lambda n: EN.skill_effect.get(getattr(skill_cs_enums.ST, n)).format(
                    **var_dict
                ),
                debug=debug,
            ),
            "skills.activation_type": build_choices(
                to_table(prev.get("skills.activation_type", {}).get("choices", {})),
                skill_cs_enums.TT,
                lambda x: getattr(skill_cs_enums.TT, x) in skill_acts_in_use,
                debug=debug,
            ),
        }
    }

    with open(output_file, "w") as outjs:
        json.dump(table, outjs, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(plac.call(main))
