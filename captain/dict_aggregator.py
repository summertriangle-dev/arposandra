from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple, Set

from libcard2.string_mgr import DictionaryAccess


TStrings = Dict[str, str]
TAltKeys = Set[str]


@dataclass
class Alternative(object):
    name: str
    code: str
    access: DictionaryAccess


class DictionaryAggregator(object):
    def __init__(self, master_dict: DictionaryAccess, choices: Dict[str, Alternative]):
        self.master = master_dict
        self.choices = choices

    # Currently unused since the servers have synced and all strings
    # should be valid (hopefully).
    def filter_strings(self, stringsd: TStrings):
        return stringsd

    def lookup_strings(
        self, stringset: Iterable[str], preferred_language: Optional[str] = None
    ) -> Tuple[TStrings, TAltKeys]:
        ss = set(stringset)

        alt = self.choices.get(preferred_language)  # type: ignore
        if not alt:
            return self.master.lookup_strings(ss), set()

        stage1 = alt.access.lookup_strings(ss)
        # stage1 = self.filter_strings(stage1)

        alt_set = set(stage1.keys())
        stage2 = self.master.lookup_strings(ss - alt_set)
        stage2.update(stage1)

        return stage2, alt_set
