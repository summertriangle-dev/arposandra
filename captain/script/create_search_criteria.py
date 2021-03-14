import gettext
import json
import os
from collections import OrderedDict
from typing import OrderedDict, Dict, List, Any

import pkg_resources
import plac

from captain.models import mine_models
from captain.models.indexer import types
from libcard2 import master, string_mgr

FIELD_TYPE_ENUM = 1000
FIELD_TYPE_ENUM_FROM_STRING_MASTER = 1001


class DFallback(object):
    def __init__(self, call):
        self.call = call

    def gettext(self, s):
        if s.startswith("kars."):
            raise ValueError(
                f"Dictionary fallback for '{s}'. This probably means you have to add it to search.pot."
            )
        return self.call(s)


def make_criteria(field: types.Field) -> dict:
    crit = {"type": field.field_type, "multi": field.multiple}

    if field.map_enum_to_id is not None:
        crit["type"] = FIELD_TYPE_ENUM
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
    for fts_field in model.fts_bond_tables:
        criteria[fts_field] = {
            "type": types.FIELD_TYPE_STRING,
            "behaviour": {"fts": True},
        }

    for field in model.fields:
        if field.behaviour and field.behaviour.get("hidden"):
            continue

        if field.field_type == types.FIELD_TYPE_COMPOSITE:
            for subfield in field.sub_fields:
                crit = make_criteria(subfield)
                criteria[f"{field.name}.{subfield.name}"] = crit
        else:
            crit = make_criteria(field)
            criteria[field.name] = crit

    return criteria


def flatten_group(dog: OrderedDict[str, list]):
    flat = []
    for key, value in dog.items():
        if value:
            flat.append({"name": key, "separator": True})
            flat.extend(value)

    return flat


K_NO_GROUP = "kars.search_criteria.card_index.member_group.unspecified"


def augment_card_schema(master: master.MasterData):
    criteria = core_schema(mine_models.CardIndex)

    subids = []
    gids = []
    groups = []
    subunits: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict()
    idols: OrderedDict[str, List[Dict[str, Any]]] = OrderedDict({K_NO_GROUP: []})
    for member in master.lookup_member_list():
        if member.group is not None and member.group not in gids:
            gids.append(member.group)
            idols[member.group_name] = []
            subunits[member.group_name] = []
            groups.append({"value": member.group, "name": member.group_name})

        if member.subunit is not None and member.subunit not in subids:
            subids.append(member.subunit)
            subunits[member.group_name].append(
                {"value": member.subunit, "name": member.subunit_name}
            )

        if member.group is not None:
            idols[member.group_name].append({"value": member.id, "name": member.name})
        else:
            idols[K_NO_GROUP].append({"value": member.id, "name": member.name})

    idols.move_to_end(K_NO_GROUP)

    criteria["member"].update(
        dict(type=FIELD_TYPE_ENUM_FROM_STRING_MASTER, choices=flatten_group(idols))
    )
    criteria["member_subunit"].update(
        dict(type=FIELD_TYPE_ENUM_FROM_STRING_MASTER, choices=flatten_group(subunits))
    )
    criteria["member_group"].update(dict(type=FIELD_TYPE_ENUM_FROM_STRING_MASTER, choices=groups))
    criteria["rarity"].update(
        dict(
            type=FIELD_TYPE_ENUM,
            choices=[
                {"name": "r", "value": 10},
                {"name": "sr", "value": 20},
                {"name": "ur", "value": 30},
            ],
        )
    )
    criteria["member_year"].update(
        dict(
            type=FIELD_TYPE_ENUM,
            choices=[
                {"name": "year_1st", "value": 1},
                {"name": "year_2nd", "value": 2},
                {"name": "year_3rd", "value": 3},
            ],
        )
    )

    return {"criteria": criteria}


def translate_schema(schm: dict, langcode: str, sid: str, mv: str, string_table: str):
    catalog = pkg_resources.resource_filename("captain", "gettext")
    search_stab = gettext.translation("search", catalog, [langcode])

    da = string_mgr.DictionaryAccess(
        os.path.join(os.environ.get("ASTOOL_STORAGE", ""), sid, "masters", mv), langcode
    )
    search_stab.add_fallback(DFallback(da.lookup_single_string))  # type: ignore

    schm["language"] = langcode
    for (key, value) in schm["criteria"].items():
        value["display_name"] = search_stab.gettext(f"kars.search_criteria.{string_table}.{key}")

        if value["type"] == FIELD_TYPE_ENUM:
            for choice in value["choices"]:
                choice["display_name"] = search_stab.gettext(
                    f"kars.search_criteria.{string_table}.{key}.{choice['name']}"
                )
                choice.pop("name")
        elif value["type"] == FIELD_TYPE_ENUM_FROM_STRING_MASTER:
            value["type"] = FIELD_TYPE_ENUM
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
    mas = master.MasterData(mp)

    card_base = augment_card_schema(mas)
    translate_schema(card_base, langcode, t_master_sid, t_master_version, "card_index")

    with open(os.path.join(destination, f"card.base.{langcode}.json"), "w") as f:
        json.dump(card_base, f, ensure_ascii=False)



if __name__ == "__main__":
    plac.call(main)
