from collections import namedtuple

Alternative = namedtuple("Alternative", ("name", "code", "access"))


class DictionaryAggregator(object):
    def __init__(self, master_dict, choices):
        self.master = master_dict
        self.choices = choices

    def lookup_strings(self, stringset, preferred_language):
        ss = set(stringset)

        alt = self.choices.get(preferred_language)
        if not alt:
            return self.master.lookup_strings(ss)

        stage1 = alt.access.lookup_strings(ss)
        stage2 = self.master.lookup_strings(ss - set(stage1.keys()))
        stage2.update(stage1)

        return stage2
