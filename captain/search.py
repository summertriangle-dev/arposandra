from tornado.web import RequestHandler
from tornado.locale import get_supported_locales

from .models.indexer import types
from .models.mine_models import CardIndex
from .dispatch import route, LanguageCookieMixin, DatabaseMixin
from . import pageutils


@route(r"/api/private/search/cards/bootstrap.json")
class APISearchBootstrap(LanguageCookieMixin, DatabaseMixin):
    BLACKLIST = ["release_dates"]

    def make_criteria(self, field):
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

    def core_schema(self):
        criteria = {}
        for field in CardIndex.fields:
            if field.name in self.BLACKLIST:
                continue

            if field.field_type == types.FIELD_TYPE_COMPOSITE:
                for subfield in field.sub_fields:
                    crit = self.make_criteria(subfield)
                    criteria[f"{field.name}.{subfield.name}"] = crit
            else:
                crit = self.make_criteria(field)
                criteria[field.name] = crit

        return criteria

    def schema(self):
        criteria = self.core_schema()

        subids = []
        gids = []
        subunits = []
        groups = []
        idols = []
        for member in self.master().lookup_member_list():
            if member.group and member.group not in gids:
                gids.append(member.group)
                groups.append({"value": member.group, "name": member.group_name})
            if member.subunit and member.subunit not in subids:
                subids.append(member.subunit)
                subunits.append({"value": member.subunit, "name": member.subunit_name})
            idols.append(
                {"value": member.id, "name": member.name_romaji,}
            )

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
                behaviour={"compare_type": "bit-set"},
            )
        )

        return {"criteria": criteria}

    def translate_schema(self, schm):
        string_src = self.settings["static_strings"].get(self.locale.code)
        for (key, value) in schm["criteria"].items():
            value["display_name"] = string_src.gettext(f"kars.search_criteria.card_index.{key}")

            if value["type"] == 1000:
                for choice in value["choices"]:
                    choice["display_name"] = string_src.gettext(
                        f"kars.search_criteria.card_index.{key}.{choice['name']}"
                    )
            elif value["type"] == 1001:
                for choice in value["choices"]:
                    choice["display_name"] = string_src.gettext(choice["name"])

    def get(self):
        schema = self.schema()
        self.translate_schema(schema)

        # self.set_header("Cache-Control", "public, max-age=86400")
        self.write(schema)


@route(r"/cards/search")
class CardSearch(LanguageCookieMixin, DatabaseMixin):
    def get(self):
        self.render("card_search_scaffold.html")
