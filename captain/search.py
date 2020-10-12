import json
import logging
from collections import OrderedDict
from datetime import datetime

import pkg_resources
from tornado.locale import get_supported_locales
from tornado.web import RequestHandler

from . import pageutils
from .dispatch import DatabaseMixin, LanguageCookieMixin, route
from .models.indexer import db_expert, types
from .models.mine_models import CardIndex


@route(r"/cards/search")
class CardSearch(LanguageCookieMixin, DatabaseMixin):
    SUPPORTED_LANGS = ["en", "ja"]

    def indexes_for_lang(self):
        if self.locale.code in self.SUPPORTED_LANGS:
            code = self.locale.code
        else:
            code = self.SUPPORTED_LANGS[0]

        return [
            self.static_url(f"search/base.{code}.json"),
            self.static_url(f"search/skills.enum.{code}.json"),
        ]

    def dictionary_for_lang(self):
        return self.static_url("search/dictionary.dummy.json")

    def get(self):
        self.render(
            "card_search_scaffold.html",
            config_indexes=self.indexes_for_lang(),
            config_dictionary=self.dictionary_for_lang(),
        )


@route("/api/private/search/cards/results.json")
class CardSearchExec(LanguageCookieMixin, DatabaseMixin):
    FIELD_BLACKLIST = ["release_dates"]

    def look_up_schema_field(self, field_name: str) -> types.Field:
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

        clean_query_presort: List[Tuple[Iterable[int], str, dict]] = []
        for field, value in query.items():
            if field.startswith("_"):
                continue

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

                    clean_query_presort.append(
                        (scmfield.order, field, {"value": value, "exclude": True})
                    )
                else:
                    if not isinstance(value, int):
                        return self._error(400, f"{field}: The value must be an integer.")

                    clean_query_presort.append(
                        (scmfield.order, field, {"value": value, "compare_type": "eq"})
                    )
            elif scmfield.field_type == types.FIELD_TYPE_INT:
                if not isinstance(value, dict) or "compare_to" not in value:
                    return self._error(400, f"{field}: Invalid integer payload.")

                value["value"] = value.pop("compare_to")
                clean_query_presort.append((scmfield.order, field, value))
            elif (
                scmfield.field_type == types.FIELD_TYPE_STRING
                or scmfield.field_type == types.FIELD_TYPE_STRINGMAX
            ):
                if not isinstance(value, str):
                    return self._error(400, f"{field}: Invalid string payload.")

                clean_query_presort.append((scmfield.order, field, {"value": str(value)}))
            elif scmfield.field_type == types.FIELD_TYPE_DATETIME:
                try:
                    clean_query_presort.append(
                        (scmfield.order, field, {"value": datetime.fromisoformat(value)})
                    )
                except ValueError:
                    return self._error(400, f"{field}: Invalid format")

        clean_query_presort.sort(key=lambda x: x[0])
        clean_query = OrderedDict(x[1:] for x in clean_query_presort)

        if "id" in clean_query:
            clean_query["id"]["return"] = True
        else:
            clean_query["id"] = {"return": True}
            clean_query.move_to_end("id", last=False)

        order_by = None
        order_desc = False

        sort_key = query.get("_sort")
        if sort_key:
            try:
                f = self.look_up_schema_field(sort_key[1:])
            except KeyError:
                pass
            else:
                order_by = sort_key[1:]
                order_desc = True if sort_key[0] == "-" else False

        if order_by in clean_query:
            clean_query[order_by]["return"] = True
        elif order_by:
            clean_query[order_by] = {"return": True}

        expert = db_expert.PostgresDBExpert(CardIndex)
        async with self.database().pool.acquire() as connection:
            res = await expert.run_query(connection, clean_query, order_by, order_desc)

        self.write({"result": [r["id"] for r in res]})
