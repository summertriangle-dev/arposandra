import gettext
import json
import os

import pkg_resources
import plac

from captain.models import mine_models
from captain.models.indexer import types
from libcard2 import master, string_mgr

BLACKLIST = ["release_dates"]


class DFallback(object):
    def __init__(self, call):
        self.call = call

    def gettext(self, s):
        return self.call(s)


def make_criteria(field: types.Field) -> dict:
    crit = {"type": field.field_type, "multi": field.multiple}

    if field.map_enum_to_id is not None:
        crit["type"] = 1000
        crit["choices"] = list(
            {"name": key, "value": value} for key, value in field.map_enum_to_id.items()
        )

    if field.length:
        crit["max_len"] = field.length

    if field.behaviour:
        crit["behaviour"] = field.behaviour

    return crit


def core_schema(model: types.Schema) -> dict:
    criteria = {}
    for field in model.fields:
        if field.name in BLACKLIST:
            continue

        if field.field_type == types.FIELD_TYPE_COMPOSITE:
            for subfield in field.sub_fields:
                crit = make_criteria(subfield)
                criteria[f"{field.name}.{subfield.name}"] = crit
        else:
            crit = make_criteria(field)
            criteria[field.name] = crit

    return criteria


def schema(master: master.MasterData):
    criteria = core_schema(mine_models.CardIndex)

    subids = []
    gids = []
    subunits = []
    groups = []
    idols = []
    for member in master.lookup_member_list():
        if member.group and member.group not in gids:
            gids.append(member.group)
            groups.append({"value": member.group, "name": member.group_name})
        if member.subunit and member.subunit not in subids:
            subids.append(member.subunit)
            subunits.append({"value": member.subunit, "name": member.subunit_name})
        idols.append({"value": member.id, "name": member.name})

    criteria["member"].update(dict(type=1001, choices=idols))
    criteria["member_subunit"].update(dict(type=1001, choices=subunits))
    criteria["member_group"].update(dict(type=1001, choices=groups))
    criteria["rarity"].update(
        dict(
            type=1000,
            choices=[
                {"name": "r", "value": 10},
                {"name": "sr", "value": 20},
                {"name": "ur", "value": 30},
            ],
        )
    )
    criteria["member_year"].update(
        dict(
            type=1000,
            choices=[
                {"name": "year_1st", "value": 1},
                {"name": "year_2nd", "value": 2},
                {"name": "year_3rd", "value": 3},
            ],
        )
    )

    return {"criteria": criteria}


def translate_schema(schm: dict, langcode: str, sid: str, mv: str):
    catalog = pkg_resources.resource_filename("captain", "gettext")
    search_stab = gettext.translation("search", catalog, [langcode])

    da = string_mgr.DictionaryAccess(
        os.path.join(os.environ.get("ASTOOL_STORAGE", ""), sid, "masters", mv), langcode
    )
    search_stab.add_fallback(DFallback(da.lookup_single_string))

    schm["language"] = langcode
    for (key, value) in schm["criteria"].items():
        value["display_name"] = search_stab.gettext(f"kars.search_criteria.card_index.{key}")

        if value["type"] == 1000:
            for choice in value["choices"]:
                choice["display_name"] = search_stab.gettext(
                    f"kars.search_criteria.card_index.{key}.{choice['name']}"
                )
                choice.pop("name")
        elif value["type"] == 1001:
            value["type"] = 1000
            for choice in value["choices"]:
                s = search_stab.gettext(choice["name"])
                choice["display_name"] = s if s else choice["name"]
                choice.pop("name")


@plac.pos("destination")
@plac.pos("langcode")
@plac.pos("master_version")
@plac.pos("master_sid")
@plac.opt("t_master_version", abbrev="t")
@plac.opt("t_master_sid", abbrev="s")
def main(
    destination, langcode, master_version, master_sid, t_master_version=None, t_master_sid=None
):
    if not t_master_version:
        t_master_version = master_version
    if not t_master_sid:
        t_master_sid = master_sid

    mp = os.path.join(os.environ.get("ASTOOL_STORAGE", ""), master_sid, "masters", master_version)
    base = schema(master.MasterData(mp))
    translate_schema(base, langcode, t_master_sid, t_master_version)

    with open(destination, "w") as f:
        json.dump(base, f, ensure_ascii=False)


if __name__ == "__main__":
    plac.call(main)
