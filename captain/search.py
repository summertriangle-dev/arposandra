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
