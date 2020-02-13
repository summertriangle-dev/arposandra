import sqlite3
import os
from collections import defaultdict
from typing import Iterable, TypeVar, Callable, Dict, Optional
from html import unescape


def batches(iterable, groups_of=500):
    if len(iterable) <= groups_of:
        yield iterable
        return

    start = 0
    while 1:
        group = iterable[start : start + groups_of]
        if not group:
            break
        yield group
        start = start + groups_of


def bucketize(iterable: Iterable[str]) -> Dict[str, Iterable[str]]:
    ret = defaultdict(lambda: [])
    for i in iterable:
        if not i:
            continue
        l, r = i.split(".", 1)
        ret[l].append(r)
    return ret


class DictionaryAccess(object):
    def __init__(self, master_path, language):
        self.master_path = master_path
        self.language = language
        self.sqlites = {}

    def get_dictionary_handle(self, key: str) -> sqlite3.Connection:
        r = self.sqlites.get(key)
        if not r:
            r = sqlite3.connect(
                "file:{0}?mode=ro".format(
                    os.path.join(self.master_path, f"dictionary_{self.language}_{key}.db")
                ),
                uri=True,
            )
            self.sqlites[key] = r
        return r

    def lookup_strings_by_key2(self, key: str, strings: Iterable[str], into: Dict[str, str]):
        sql = self.get_dictionary_handle(key)
        lastlen = 0
        for page in batches(strings):
            if len(page) != lastlen:
                query = "SELECT id, message FROM m_dictionary WHERE id IN ({0})".format(
                    ",".join("?" * len(page))
                )
                lastlen = len(page)
            for k, m in sql.execute(query, page):
                into[f"{key}.{k}"] = unescape(m)

    def lookup_strings_by_key(self, key: str, strings: Iterable[str]) -> Dict[str, str]:
        a = {}
        self.lookup_strings_by_key2(key, strings, a)
        return a

    def lookup_strings(self, stringset: Iterable[str]) -> Dict[str, str]:
        ss = set(stringset)
        bykey = bucketize(ss)
        ret = {}
        for key, values in bykey.items():
            self.lookup_strings_by_key2(key, values, ret)

        return ret

    # Do not use this method. It is only here for the
    # SkillEffectDescriberContext protocol.
    def lookup_single_string(self, key) -> Optional[str]:
        return self.lookup_strings((key,)).get(key)

    def close(self):
        for v in self.sqlites.values():
            v.close()
        self.sqlites = {}
