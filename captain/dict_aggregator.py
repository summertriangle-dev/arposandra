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

    def filter_strings(self, stringsd: TStrings):
        to_remove = []

        # to be removed, hopefully when the sync happens
        for key, value in stringsd.items():
            if "仮" in value:
                to_remove.append(key)

            if key == "k.passive_skill_name_321030111":
                to_remove.append(key)

            if key == "k.passive_skill_name_321030121":
                to_remove.append(key)

        for k in to_remove:
            stringsd.pop(k)

        return stringsd

    def lookup_strings(
        self, stringset: Iterable[str], preferred_language: Optional[str] = None
    ) -> Tuple[TStrings, TAltKeys]:
        ss = set(stringset)

        alt = self.choices.get(preferred_language)  # type: ignore
        if not alt:
            return self.master.lookup_strings(ss), set()

        stage1 = alt.access.lookup_strings(ss)
        stage1 = self.filter_strings(stage1)

        alt_set = set(stage1.keys())
        stage2 = self.master.lookup_strings(ss - alt_set)
        stage2.update(stage1)

        return stage2, alt_set
