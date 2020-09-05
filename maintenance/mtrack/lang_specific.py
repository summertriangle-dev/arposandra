import re
from typing import Callable

LANG_JP_EVT_FIRST_HALF = "（前編）"
LANG_JP_EVT_SECOND_HALF = "（後編）"
LANG_JP_FES_MARKER = "フェス開催"
LANG_JP_PICKUP_MARKER = "ピックアップガチャ"
LANG_JP_EVT_OMNIBUS_MARKER = "スクールアイドル紹介"

T_EVENT_TIE = 1
T_PICK_UP = 2
T_FES = 3
T_ELSE = 4
T_IGNORE = -1


def gacha_label_from_name_jp(name: str) -> int:
    if LANG_JP_FES_MARKER in name:
        return T_FES
    elif LANG_JP_PICKUP_MARKER in name:
        return T_PICK_UP
    elif LANG_JP_EVT_OMNIBUS_MARKER in name or LANG_JP_EVT_FIRST_HALF in name:
        return T_EVENT_TIE
    elif LANG_JP_EVT_SECOND_HALF in name:
        return T_IGNORE
    else:
        return T_ELSE


def gacha_label_from_name_en(name: str) -> int:
    # Hopefully they don't change their style.
    name = name.lower()
    if name.startswith("scout in") and name.endswith("festival!"):
        return T_FES
    elif name.endswith("spotlight scouting"):
        return T_PICK_UP
    elif name.endswith("school idol lineup") or "scouting (part 1)" in name:
        return T_EVENT_TIE
    elif "scouting (part 2)" in name:
        return T_IGNORE
    else:
        return T_ELSE


def cleanup_name_jp(etyp: int, name: str) -> str:
    if etyp == 1:
        m = re.search(r"(.*ピックアップガチャ|.*ガチャ|.*フェス)", name)
        return m.group(1) if m else name
    else:
        m = re.search(r"「(.+)」", name)
        return m.group(1) if m else name


def cleanup_name_en(etyp: int, name: str) -> str:
    if etyp == 1:
        m = re.sub(r"school idol lineup", "", name, flags=re.IGNORECASE).strip()
        return m

    return name


def get_name_clean_func(tag: str) -> Callable[[int, str], str]:
    if tag == "jp":
        return cleanup_name_jp
    elif tag == "en":
        return cleanup_name_en
    else:
        raise ValueError("Invalid tag. You need to add support for this language to newsminer!")


def get_gacha_label_func(tag: str) -> Callable[[str], int]:
    if tag == "jp":
        return gacha_label_from_name_jp
    elif tag == "en":
        return gacha_label_from_name_en
    else:
        raise ValueError("Invalid tag. You need to add support for this language to newsminer!")
