from . import skills_en
from . import wave_en

_s_registry = {"en": skills_en.EN}

_w_registry = {"en": wave_en.EN}


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
