import logging
import sqlite3
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
            m_fields.append(f"{multi_field.name} {self.sql_type(field)}")
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

            stmt = self.m_cache.get(cache_key)
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
                self.m_cache[cache_key] = stmt
                log_sql.debug("%s", stmt)

            await connection.execute(stmt, *values)
