from . import skills_en, skills_ja
from . import wave_en, wave_ja

_s_registry = {"en": skills_en.EN, "ja": skills_ja.JA}

_w_registry = {"en": wave_en.EN, "ja": wave_ja.JA}


def skill_describer_for_locale(lc):
    if lc in _s_registry:
        return _s_registry[lc]

    firstpart = lc.split("_")[0]
    if firstpart in _s_registry:
        return _s_registry[firstpart]

    return _s_registry["en"]


def wave_describer_for_locale(lc):
    if lc in _w_registry:
        return _w_registry[lc]

    firstpart = lc.split("_")[0]
    if firstpart in _w_registry:
        return _w_registry[firstpart]

    return _w_registry["en"]
