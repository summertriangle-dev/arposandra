import os
import struct
import sqlite3
import tempfile
import imghdr
import binascii
import atexit
import logging
import asyncio
from weakref import WeakSet
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor
from multiprocessing import Pipe

from tornado.ioloop import IOLoop
from tornado.autoreload import add_reload_hook

import hwdecrypt
from .synthetic import stack_card

G_ATEXIT_REGISTERED = False
G_ACTIVE_PROCESSPOOLS = WeakSet()


def shutdown_all_pools():
    for p in G_ACTIVE_PROCESSPOOLS:
        print(p)
        p.shutdown(wait=True)


add_reload_hook(shutdown_all_pools)


def to_unsigned(i):
    return struct.unpack("<I", struct.pack("<i", i))[0]


class ExtractFailure(Exception):
    def __init__(self, reason):
        super().__init__(ExtractFailure.reason_string(reason))
        self.reason = reason

    @staticmethod
    def reason_string(r):
        if r == 1:
            return "Asset not found."
        if r == 2:
            return "Cache file appears to be corrupt. Try rebuilding it with package_list_tool."
        if r == 3:
            return "IO error."
        if r == 4:
            return "Unrecognized format."


class ExtractContext(object):
    def __init__(self, master, cache):
        self.asset_db = sqlite3.connect(f"file:{master}?mode=ro", uri=True)
        self.cache = cache
        self.pool = None

    def get_pool(self):
        global G_ATEXIT_REGISTERED
        if not self.pool:
            if not G_ATEXIT_REGISTERED:
                atexit.register(shutdown_all_pools)
                G_ATEXIT_REGISTERED = True
            self.pool = ProcessPoolExecutor()
            G_ACTIVE_PROCESSPOOLS.add(self.pool)
        return self.pool

    def change_asset_db(self, newdb):
        self.asset_db.disconnect()
        self.asset_db = sqlite3.connect(f"file:{newdb}?mode=ro")

    def get_texture_info(self, key):
        row = self.asset_db.execute(
            """SELECT pack_name, head, size, key1, key2 
            FROM texture WHERE asset_path = ?""",
            (key,),
        )
        info = row.fetchone()
        if not info:
            raise ExtractFailure(1)

        return (*info, 0x3039)

    def get_texture(self, key, intobuf):
        pack_name, head, size, key1, key2, _ = self.get_texture_info(key)
        pack = os.path.join(self.cache, f"pkg{pack_name[0]}", pack_name)
        k1 = to_unsigned(key1)
        k2 = to_unsigned(key2)

        keyset = hwdecrypt.Keyset(k1, k2)
        with open(pack, "rb") as f:
            f.seek(head)

            while size > 0:
                nread = f.readinto(intobuf)
                hwdecrypt.decrypt(keyset, intobuf)
                if nread > size:
                    yield (intobuf, size)
                else:
                    yield (intobuf, nread)
                size -= nread

    async def get_cardicon(self, image_asset_id, format, frame_num, role_num, attr_num):
        pack, *texinfo = self.get_texture_info(image_asset_id)
        pack = os.path.join(self.cache, f"pkg{pack[0]}", pack)
        load_args = (pack, *texinfo)
        result, data = await IOLoop.current().run_in_executor(
            self.get_pool(), stack_card, load_args, format, frame_num, role_num, attr_num
        )

        if result > 0:
            raise ExtractFailure(result)

        return data
