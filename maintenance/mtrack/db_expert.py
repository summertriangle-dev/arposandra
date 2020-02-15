import sqlite3
from typing import TypeVar, Generic

import asyncpg

from . import indexer

T = TypeVar("T")


class SQLiteDBExpert(Generic[T]):
    def __init__(self, schema: indexer.Schema[T], db_handle: sqlite3.Connection):
        self.schema = schema
        self.connection = db_handle

    def sql_type(self, field: indexer.Field):
        if field.field_type == indexer.FIELD_TYPE_INT:
            return "INT"
        elif field.field_type == indexer.FIELD_TYPE_STRING:
            return "TEXT"

    def create_tables(self):
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
                f"CREATE TABLE IF NOT EXISTS {self.schema.table}__{multi_field.name} ({', '.join(m_fields)})"
            )
            m_fields.pop()

        cur.close()
        self.connection.commit()

    def add_object(self, it: T):
        cur = self.connection.cursor()
        expert = self.schema.expert(it)

        single = tuple(
            field.transform(getattr(expert, field.name)())
            for field in self.schema.fields[: self.schema.first_multi_index]
        )

        cur.execute(
            f"INSERT INTO {self.schema.table} VALUES ({', '.join('?' * len(single))})", single
        )

        multi = [
            field.transform(getattr(expert, field.name)())
            for field in self.schema.fields[: self.schema.first_multi_index]
            if field.primary
        ]
        qm = ", ".join("?" * (len(multi) + 1))
        for field in self.schema.fields[self.schema.first_multi_index :]:
            stmt = f"INSERT INTO {self.schema.table}__{field.name} VALUES ({qm})"
            for nv in field.transform(getattr(expert, field.name)()):
                multi.append(nv)
                cur.execute(stmt, multi)
                multi.pop()


class PostgresDBExpert(Generic[T]):
    def __init__(self, schema: indexer.Schema[T], pool):
        self.schema = schema
        self.pool = pool

    def sql_type(self, field: indexer.Field):
        if field.field_type == indexer.FIELD_TYPE_INT:
            return "INT"
        elif field.field_type == indexer.FIELD_TYPE_STRING:
            return "TEXT"

    async def create_tables(self):
        async with self.pool.acquire() as c, c.transaction():
            pk_header = []
            fields = []
            for field in self.schema.fields[: self.schema.first_multi_index]:
                stmt = f"{field.name} {self.sql_type(field)}"
                fields.append(stmt)
                if field.primary:
                    pk_header.append(stmt)

            fields.append(f"PRIMARY KEY ( {', '.join(pk.name for pk in self.schema.primary_key)} )")

            await c.execute(f"CREATE TABLE IF NOT EXISTS {self.schema.table} ({', '.join(fields)})")

            for multi_field in self.schema.fields[self.schema.first_multi_index :]:
                m_fields = pk_header
                m_fields.append(f"{multi_field.name} {self.sql_type(field)}")
                await c.execute(
                    f"CREATE TABLE IF NOT EXISTS {self.schema.table}__{multi_field.name} ({', '.join(m_fields)})"
                )
                m_fields.pop()

    async def add_object(self, connection: asyncpg.Connection, it: T):
        expert = self.schema.expert(it)

        single = tuple(
            field.transform(getattr(expert, field.name)())
            for field in self.schema.fields[: self.schema.first_multi_index]
        )

        await connection.execute(
            f"INSERT INTO {self.schema.table} VALUES ({', '.join(f'${x + 1}' for x in range(len(single)))})",
            *single,
        )

        multi = [
            field.transform(getattr(expert, field.name)())
            for field in self.schema.fields[: self.schema.first_multi_index]
            if field.primary
        ]
        qm = ", ".join(f"${x + 1}" for x in range((len(multi) + 1)))
        for field in self.schema.fields[self.schema.first_multi_index :]:
            stmt = f"INSERT INTO {self.schema.table}__{field.name} VALUES ({qm})"
            for nv in field.transform(getattr(expert, field.name)()):
                multi.append(nv)
                await connection.execute(stmt, *multi)
                multi.pop()
