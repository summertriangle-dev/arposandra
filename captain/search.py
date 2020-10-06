import json
import logging
import pkg_resources

from datetime import datetime

from tornado.web import RequestHandler
from tornado.locale import get_supported_locales

from .models.indexer import types, db_expert
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


@route("/api/private/search/cards/results.json")
class CardSearchExec(LanguageCookieMixin, DatabaseMixin):
    FIELD_BLACKLIST = ["release_dates"]

    def look_up_schema_field(self, field_name):
        names = field_name.split(".")
        assert len(names) > 0

        if names[0] in self.FIELD_BLACKLIST or field_name in self.FIELD_BLACKLIST:
            raise KeyError(names[0])

        root = CardIndex[names[0]]
        for name in names[1:]:
            root = root[name]

        return root

    def _error(self, status, message):
        self.set_status(status)
        self.write({"error": message})
        self.finish()

    async def post(self):
        try:
            query = json.loads(self.request.body)
        except json.JSONDecodeError:
            self.set_status(400)
            self.write({"error": "Invalid payload."})
            return

        clean_query = {}
        for field, value in query.items():
            try:
                scmfield = self.look_up_schema_field(field)
            except KeyError:
                return self._error(400, f"Unknown field: {field}")

            behaviour = scmfield.behaviour or {}

            if scmfield.field_type == types.FIELD_TYPE_INT and (
                scmfield.map_enum_to_id is not None or behaviour.get("captain_treat_as") == "enum"
            ):
                if behaviour.get("compare_type") == "bit-set":
                    if not isinstance(value, list) or not all(isinstance(x, int) for x in value):
                        return self._error(
                            400, f"{field}: The value must be a list of integers for bit-sets."
                        )

                    clean_query[field] = {"value": value, "exclude": True}
                else:
                    if not isinstance(value, int):
                        return self._error(400, f"{field}: The value must be an integer.")

                    clean_query[field] = {"value": value, "compare_type": "eq"}
            elif scmfield.field_type == types.FIELD_TYPE_INT:
                if not isinstance(value, dict) or "compare_to" not in value:
                    return self._error(400, f"{field}: Invalid integer payload.")

                value["value"] = value.pop("compare_to")
                clean_query[field] = value
            elif (
                scmfield.field_type == types.FIELD_TYPE_STRING
                or scmfield.field_type == types.FIELD_TYPE_STRINGMAX
            ):
                if not isinstance(value, str):
                    return self._error(400, f"{field}: Invalid string payload.")

                clean_query[field] = {"value": str(value)}
            elif scmfield.field_type == types.FIELD_TYPE_DATETIME:
                try:
                    clean_query[field] = {"value": datetime.fromisoformat(value)}
                except ValueError:
                    return self._error(400, f"{field}: Invalid format")

        if "id" in clean_query:
            clean_query["id"]["return"] = True
        else:
            clean_query["id"] = {"return": True}

        expert = db_expert.PostgresDBExpert(CardIndex)
        async with self.database().pool.acquire() as connection:
            res = await expert.run_query(connection, clean_query)

        self.write({"result": [r["id"] for r in res]})
        self.finish()
