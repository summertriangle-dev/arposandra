import logging
import sqlite3
import time
from datetime import datetime
from typing import Dict, Generic, TypeVar, cast

import asyncpg

from . import types

T = TypeVar("T")

log_sql = logging.getLogger(f"{__name__}.sql")


class SQLiteDBExpert(Generic[T]):
    def __init__(self, schema: types.Schema[T], db_handle: sqlite3.Connection):
        self.schema = schema
        self.connection = db_handle
        self.cache: Dict[str, str] = {}
        self.m_cache: Dict[str, str] = {}

    def sql_type(self, field: types.Field):
        if field.field_type == types.FIELD_TYPE_INT:
            return "INT"
        elif field.field_type == types.FIELD_TYPE_STRING:
            return "TEXT"
        elif field.field_type == types.FIELD_TYPE_DATETIME:
            return "INT"
        elif field.field_type == types.FIELD_TYPE_STRINGMAX:
            return f"VARCHAR({field.length})"

    @staticmethod
    def map_down(self, value, field_type):
        if field_type == types.FIELD_TYPE_DATETIME:
            return cast(value, datetime).timestamp()
        return value

    async def create_tables(self):
        cur = self.connection.cursor()

        pk_header = []
        fields = []
        for field in self.schema.fields[: self.schema.first_multi_index]:
            stmt = f"{field.name} {self.sql_type(field)}"
            fields.append(stmt)
            if field.primary:
                pk_header.append(stmt)

        fields.append(f"PRIMARY KEY ( {', '.join(pk.name for pk in self.schema.primary_key)} )")

        cur.execute(f"CREATE TABLE IF NOT EXISTS {self.schema.table} ({', '.join(fields)})")

        for multi_field in self.schema.fields[self.schema.first_multi_index :]:
            m_fields = pk_header
            m_fields.append(f"{multi_field.name} {self.sql_type(multi_field)}")
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.schema.table}__{multi_field.name} (
                    {', '.join(m_fields)} ,
                    PRIMARY KEY ( {', '.join(pk.name for pk in self.schema.primary_key)}, {multi_field.name} )
                )
                """
            )
            m_fields.pop()

        cur.close()
        self.connection.commit()

    async def add_object(self, it: T, overwrite=True):
        cur = self.connection.cursor()
        (sfields, svalues), multi = self.schema.sql_tuples_from_object(it)

        columns = ",".join(sfields)
        cache_key = columns + str(overwrite)
        stmt = self.cache.get(cache_key)
        if not stmt:
            stmt = f"""
                INSERT INTO {self.schema.table} ({columns}) 
                VALUES ({', '.join('?' * len(svalues))})
                ON CONFLICT ({', '.join(pk.name for pk in self.schema.primary_key)})
            """

            if overwrite:
                stmt += f"""
                DO UPDATE SET {", ".join(
                    "{0} = excluded.{0}".format(name) for name in sfields
                )}
                """
            else:
                stmt += "DO NOTHING"

            log_sql.debug("%s", stmt)
            self.cache[cache_key] = stmt

        cur.execute(stmt, svalues)

        cleanup_column = None
        for column, values in multi:
            if overwrite and column != cleanup_column:
                cleanup_column = column
                cleanup_frag = [f"DELETE FROM {self.schema.table}__{column} WHERE 1"]
                for k in self.schema.primary_key:
                    cleanup_frag.append(f"AND {k.name} = ?")
                cleanup_stmt = "\n".join(cleanup_frag)
                log_sql.debug("%s", cleanup_stmt)
                cur.execute(cleanup_stmt, values[: len(self.schema.primary_key)])

            stmt = self.m_cache.get(column)
            if not stmt:
                pk = [pk.name for pk in self.schema.primary_key]
                pk.append(column)

                pks = ", ".join(pk)
                stmt = f"""
                    INSERT INTO {self.schema.table}__{column} VALUES ({','.join('?' * len(values))})
                    ON CONFLICT ({pks}) DO NOTHING
                """
                self.m_cache[cache_key] = stmt
                log_sql.debug("%s", stmt)

            cur.execute(stmt, values)


class PostgresDBExpert(Generic[T]):
    def __init__(self, schema: types.Schema[T]):
        self.schema = schema
        self.cache: Dict[str, str] = {}
        self.m_cache: Dict[str, str] = {}

    def sql_type(self, field: types.Field):
        if field.field_type == types.FIELD_TYPE_INT:
            return "INT"
        elif field.field_type == types.FIELD_TYPE_STRING:
            return "TEXT"
        elif field.field_type == types.FIELD_TYPE_DATETIME:
            return "TIMESTAMP"
        elif field.field_type == types.FIELD_TYPE_STRINGMAX:
            return f"VARCHAR({field.length})"

    async def create_tables(self, c: asyncpg.Connection, temporary=False, temp_prefix="TEMP__"):
        pk_header = []
        fields = []
        for field in self.schema.fields[: self.schema.first_multi_index]:
            stmt = f"{field.name} {self.sql_type(field)}"
            fields.append(stmt)
            if field.primary:
                pk_header.append(stmt)

        pk = ", ".join(pk.name for pk in self.schema.primary_key)
        fields.append(f"PRIMARY KEY ( {pk} )")

        if temporary:
            await c.execute(
                f"CREATE TEMP TABLE {temp_prefix}{self.schema.table} ({', '.join(fields)}) "
                "ON COMMIT DROP"
            )
        else:
            await c.execute(f"CREATE TABLE IF NOT EXISTS {self.schema.table} ({', '.join(fields)})")

        for multi_field in self.schema.fields[self.schema.first_multi_index :]:
            m_fields = pk_header[:]
            if multi_field.field_type == types.FIELD_TYPE_COMPOSITE:
                assert multi_field.sub_fields is not None

                m_fields.extend(
                    f"{subfield.name} {self.sql_type(subfield)}"
                    for subfield in multi_field.sub_fields
                )
                pk_stmt = f"{pk}," + ",".join(
                    subfield.name for subfield in multi_field.sub_fields if subfield.primary
                )
            else:
                m_fields.append(f"{multi_field.name} {self.sql_type(multi_field)}")
                pk_stmt = f"{pk}, {multi_field.name}"

            if temporary:
                await c.execute(
                    f"""CREATE TEMP TABLE {temp_prefix}{self.schema.table}__{multi_field.name} (
                        {', '.join(m_fields)}, PRIMARY KEY ( {pk_stmt} ) 
                        ) ON COMMIT DROP
                    """
                )
            else:
                await c.execute(
                    f"""CREATE TABLE IF NOT EXISTS {self.schema.table}__{multi_field.name} (
                            {', '.join(m_fields)}, PRIMARY KEY ( {pk_stmt} ));
                        CREATE INDEX IF NOT EXISTS {self.schema.table}__{multi_field.name}__auto
                            ON {self.schema.table}__{multi_field.name}
                            ({pk_stmt})
                    """
                )

    async def add_object(self, connection: asyncpg.Connection, it: T, overwrite=True, prefix=""):
        (sfields, svalues), multi = self.schema.sql_tuples_from_object(it)

        columns = ",".join(sfields)
        cache_key = "|".join((columns, str(overwrite), prefix))
        stmt = self.cache.get(cache_key)
        if not stmt:
            stmt = f"""
                INSERT INTO {prefix}{self.schema.table} ({columns}) 
                VALUES ({', '.join(f'${x + 1}' for x in range(len(svalues)))})
                ON CONFLICT ({', '.join(pk.name for pk in self.schema.primary_key)}) 
            """

            if overwrite:
                stmt += f"""
                DO UPDATE SET {", ".join(
                    "{0} = excluded.{0}".format(name) for name in sfields
                )}
                """
            else:
                stmt += "DO NOTHING"

            log_sql.debug("%s", stmt)
            self.cache[cache_key] = stmt

        await connection.execute(stmt, *svalues)

        cleanup_column = None
        for column, values in multi:
            if overwrite and column != cleanup_column:
                cleanup_column = column
                cleanup_frag = [f"DELETE FROM {prefix}{self.schema.table}__{column} WHERE TRUE"]
                for idx, k in enumerate(self.schema.primary_key):
                    cleanup_frag.append(f"AND {k.name} = ${idx + 1}")
                cleanup_stmt = "\n".join(cleanup_frag)
                log_sql.debug("%s", cleanup_stmt)
                await connection.execute(cleanup_stmt, *values[: len(self.schema.primary_key)])

            ck_multi = "|".join((cache_key, column))
            stmt = self.m_cache.get(ck_multi)
            if not stmt:
                pk = [pk.name for pk in self.schema.primary_key]
                if self.schema[column].field_type == types.FIELD_TYPE_COMPOSITE:
                    pk.extend(x.name for x in self.schema[column].sub_fields if x.primary)
                else:
                    pk.append(column)

                pks = ", ".join(pk)
                stmt = f"""
                    INSERT INTO {prefix}{self.schema.table}__{column} VALUES 
                    ({', '.join(f'${x + 1}' for x in range(len(values)))})
                    ON CONFLICT ({pks}) DO NOTHING
                """
                self.m_cache[ck_multi] = stmt
                log_sql.debug("%s", stmt)

            await connection.execute(stmt, *values)

    def look_up_schema_field(self, field_name):
        names = field_name.split(".")
        assert len(names) > 0

        root = self.schema[names[0]]
        table = [self.schema.table]
        for name in names[1:]:
            table.append(root.name)
            root = root[name]

        return root, "__".join(table)

    def _get_op(self, ops, equal=True):
        if ops == "eq" and equal:
            return "="
        elif ops == "lt":
            return "<"
        elif ops == "gt":
            return ">"
        elif ops == "gte":
            return ">="
        elif ops == "lte":
            return "<="

        raise ValueError("invalid operator")

    def build_query(self, crit_list, fts_bond_list, order_by=None, order_desc=False):
        fetchresult = []
        wheres = []
        joins = set()
        parameters = []
        order_clause = ""

        pkspec = ", ".join(pk.name for pk in self.schema.primary_key)
        for (field_name, filter_value) in crit_list.items():
            field, tablename = self.look_up_schema_field(field_name)
            if filter_value.get("return"):
                fetchresult.append(f"{tablename}.{field.name}")

            if tablename != self.schema.table:
                joins.add(f"INNER JOIN {tablename} USING ({pkspec})")

            raw_value = filter_value.get("value")
            if raw_value is None:
                continue

            if field.field_type == types.FIELD_TYPE_INT:
                if isinstance(raw_value, int):
                    compare_type = self._get_op(filter_value.get("compare_type", "eq"))
                    wheres.append(f"{tablename}.{field.name} {compare_type} ${len(parameters) + 1}")
                else:
                    compare_type = "!= ALL" if filter_value.get("exclude") else "= ANY"
                    wheres.append(
                        f"{tablename}.{field.name} {compare_type} (${len(parameters) + 1}::int[])"
                    )

                parameters.append(raw_value)
            elif (
                field.field_type == types.FIELD_TYPE_STRING
                or field.field_type == types.FIELD_TYPE_STRINGMAX
            ):
                if field.length is not None and len(raw_value) > field.length:
                    raise types.NoLogicalResult(field_name)

                compare_type = "!=" if filter_value.get("exclude") else "="
                wheres.append(f"{tablename}.{field.name} {compare_type} ${len(parameters) + 1}")
                parameters.append(raw_value)
            elif field.field_type == types.FIELD_TYPE_DATETIME:
                compare_type = self._get_op(filter_value["compare_type"], equal=False)

                wheres.append(f"{tablename}.{field.name} {compare_type} ${len(parameters) + 1}")
                parameters.append(raw_value)

        for fts_bond_table_name, (langid, words) in fts_bond_list.items():
            if fts_bond_table_name not in self.schema.fts_bond_tables:
                continue

            pks = []
            for pk in self.schema.primary_key:
                pks.append(
                    f"{self.schema.table}.{pk.name} = {fts_bond_table_name}.referent_{pk.name}"
                )
            joins.add(f"INNER JOIN {fts_bond_table_name} ON ({' AND '.join(pks)})")
            wheres.append(
                f"{fts_bond_table_name}.terms @@ plainto_tsquery(${len(parameters) + 1}, ${len(parameters) + 2})"
            )
            parameters.append(langid)
            parameters.append(words)

        if order_by:
            field, tablename = self.look_up_schema_field(order_by)
            order_clause = f"ORDER BY {tablename}.{field.name} {'DESC' if order_desc else 'ASC'}"

        return (
            f"""SELECT DISTINCT {', '.join(fetchresult)} FROM {self.schema.table} {' '.join(joins)}
            WHERE {' AND '.join(wheres)} {order_clause}""",
            parameters,
        )

    async def run_query(
        self,
        connection: asyncpg.Connection,
        crit_list,
        fts_bond_list=None,
        order_by=None,
        order_desc=False,
    ):
        # t = time.monotonic_ns()
        query, args = self.build_query(crit_list, fts_bond_list or {}, order_by, order_desc)
        # logging.info("Query build time: %d", time.monotonic_ns() - t)
        # logging.debug("%s %s", query, args)
        return await connection.fetch(query, *args)
