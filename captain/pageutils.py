import hashlib
import hmac
import os
import binascii
import base64
import logging
import json
from typing import Dict, Set
from tornado.escape import squeeze, xhtml_escape

import libcard2.localization
from libcard2.utils import icon_frame_info

UI_METHODS = {
    # "image_url_reify": image_url_reify,
    # "tlinject": tlinject,
    # "format_ordinal": format_ordinal,
    # "tlinject_static": tlinject_static,
    # "format_skill_effect": format_skill_effect,
    # "format_skill_target": format_skill_target,
    # "format_card_role_effect": format_card_role_effect
}


def export(f):
    UI_METHODS[f.__name__] = f
    return f


G_SECRET = None


def get_as_secret():
    global G_SECRET
    if G_SECRET is not None:
        return G_SECRET or None

    hex = os.environ.get("AS_ASSET_JIT_SECRET")
    if hex:
        G_SECRET = binascii.unhexlify(hex) or 0
    else:
        G_SECRET = 0
    return G_SECRET or None


@export
def get_skill_describer(handler):
    code = handler.locale.code
    return libcard2.localization.skill_describer_for_locale(code)


TLINJECT_EMPTY: Dict[str, str] = {}
TLINJECT_ALT_EMPTY: Set[str] = set()


@export
def tlinject_supported_languages(handler):
    return " ".join(handler.settings["db_coordinator"].tlinject_database.supported_languages)


@export
def tlinject(handler, s, key_is_pt=False, *, mock=False):
    try:
        base, alt_set = handler._tlinject_base
    except AttributeError:
        base = TLINJECT_EMPTY
        alt_set = TLINJECT_ALT_EMPTY
        logging.warn("TLInject users should have a _tlinject_base dict")

    secret = handler.settings["db_coordinator"].tlinject_database.secret
    if secret:
        my = hmac.new(secret, s.encode("utf8"), hashlib.sha224).digest()[:12]
        my = base64.urlsafe_b64encode(my).decode("ascii").rstrip("=")
    else:
        my = ""

    data = []

    if mock:
        data.append('data-mock="1"')

    if s in alt_set:
        data.append('data-overlay="1"')

    pretranslated = base.get(s, None)
    if pretranslated:
        if not key_is_pt:
            data.append(f'data-tlik="{xhtml_escape(s)}"')
        s = pretranslated

    all_data = " ".join(data)
    return squeeze(
        f"""<span class="tlinject" data-assr="{my}" {all_data}>{xhtml_escape(s)}</span>"""
    )


@export
def tlinject_static(handler, s, escape=True):
    try:
        base = handler._tlinject_base[0]
    except AttributeError:
        base = TLINJECT_EMPTY
        logging.warn("TLInject users should have a _tlinject_base dict")

    gt = handler.settings["static_strings"].get(handler.locale.code, "en")
    ss = gt.gettext(s)
    if ss is None:
        ss = base.get(s, s)
    if escape:
        return f"<span>{xhtml_escape(ss)}</span>"
    return ss


def _format_grade_en(n):
    SUFFIXES = {1: "st", 2: "nd", 3: "rd"}
    if 1 <= (n % 10) <= 3 and n // 10 != 1:
        suff = SUFFIXES[n % 10]
    else:
        suff = "th"
    return f"{n}{suff} Year"


def _format_grade_ja(n):
    return f"{n}年生"


@export
def format_grade(handler, n):
    if handler.locale.code == "ja":
        return _format_grade_ja(n)
    return _format_grade_en(n)

# Colour coding tags for first skill effect (green)
SKILL_EFFECT_FORMAT_ARGS = {
    "let": "<span class='let'>",
    "var": "<span class='var'>",
    "end": "</span>",
}

# and second effect (blue)
SKILL_EFFECT_FORMAT_ARGS_SEC = {
    "let": "<span class='let2'>",
    "var": "<span class='var2'>",
    "end": "</span>",
}

@export
def format_skill_effect(handler, skill):
    es = get_skill_describer(handler).format_effect(
        skill,
        format_args=SKILL_EFFECT_FORMAT_ARGS,
        format_args_sec=SKILL_EFFECT_FORMAT_ARGS_SEC
    )
    
    if not es:
        return f"{tlinject_static(handler, skill.description)} ({skill.levels[0].effect_type})"
    
    return es


@export
def format_skill_target(handler, skill, card=None):
    base = handler.settings["static_strings"].get(handler.locale.code, "en")
    target_text = get_skill_describer(handler).format_target(
        skill, base, card,
        format_args=SKILL_EFFECT_FORMAT_ARGS,
        format_args_sec=SKILL_EFFECT_FORMAT_ARGS_SEC
    )
    
    if not target_text:
        return ""

    return xhtml_escape(handler.locale.translate("Card.SkillTargets{what}")).format(
        what=target_text
    )


@export
def format_wave_desc(handler, wave):
    try:
        base = handler._tlinject_base[0]
    except AttributeError:
        base = {}
        logging.warn("TLInject users should have a _tlinject_base dict")

    return libcard2.localization.wave_describer_for_locale(handler.locale.code).translate(
        wave.origin_lang, base.get(wave.name, wave.name)
    )


def _divint(value):
    vf = value / 100
    vi = value // 100
    if vf == vi:
        return f"{vi}%"
    else:
        return f"{vf}%"


@export
def format_card_role_effect(handler, effect):
    rotation = "?"
    if effect.change_effect_type == 1:
        rotation = f"Add {_divint(effect.change_effect_value)} of appeal to voltage"
    elif effect.change_effect_type == 2:
        rotation = f"Restore {_divint(effect.change_effect_value)} of stamina"
    elif effect.change_effect_type == 3:
        rotation = f"Add {effect.change_effect_value} to SP gauge"
    elif effect.change_effect_type == 4:
        rotation = f"{effect.change_effect_value} less notes needed to rotate again"

    if effect.positive_type == 1:
        passive_p = f"+{_divint(effect.positive_value)} appeal"
    elif effect.positive_type == 2:
        passive_p = f"+{_divint(effect.positive_value)} SP gain"
    elif effect.positive_type == 3:
        passive_p = f"-{_divint(effect.positive_value)} damage"
    elif effect.positive_type == 4:
        passive_p = f"+{_divint(effect.positive_value)} skill activation rate"

    if effect.negative_type == 1:
        passive_n = f"-{_divint(effect.negative_value)} appeal"
    elif effect.negative_type == 2:
        passive_n = f"-{_divint(effect.negative_value)} SP gain"
    elif effect.negative_type == 3:
        passive_n = f"+{_divint(effect.negative_value)} damage"
    elif effect.negative_type == 4:
        passive_n = f"-{_divint(effect.negative_value)} skill activation rate"

    return f"""<b>Rotation Effect:</b> {rotation}<br>
        <b>Passive Effect:</b> {passive_p}, {passive_n}"""


@export
def card_has_full_bg(handler, card):
    return card.rarity > 10


@export
def image_url_reify(handler, asset_tag, ext=None, region=None):
    try:
        base = handler._reified_tags
    except AttributeError:
        handler._reified_tags = base = {}

    cache_key = f"{region}${asset_tag}"
    if cache_key in base:
        return base[cache_key]

    my = hmac.new(get_as_secret(), asset_tag.encode("utf8"), hashlib.sha224).digest()[:10]
    my = base64.urlsafe_b64encode(my).decode("ascii").rstrip("=")
    isr = handler.settings["image_server"]
    url_asset_tag = base64.urlsafe_b64encode(asset_tag.encode("utf8")).decode("ascii").rstrip("=")
    rtag = f"/{region}" if region else ""
    if ext:
        signed = f"{isr}/i{rtag}/-{url_asset_tag}/{my}.{ext}"
    else:
        signed = f"{isr}/i{rtag}/-{url_asset_tag}/{my}"

    base[cache_key] = signed
    return signed


@export
def card_icon_url(handler, card, appearance, ext="jpg"):
    try:
        base = handler._reified_tags
    except AttributeError:
        handler._reified_tags = base = {}

    frame_num = card.rarity // 10
    role_num = card.role
    attr_num = card.attribute

    fspec = icon_frame_info(frame_num, role_num, attr_num)
    first = (
        base64.urlsafe_b64encode(appearance.thumbnail_asset_path.encode("utf8"))
        .decode("ascii")
        .rstrip("=")
    )
    key = f"ci/{fspec}/-{first}"

    if key in base:
        return base[key]

    assr = hmac.new(get_as_secret(), key.encode("utf8"), hashlib.sha224).digest()[:10]
    assr = base64.urlsafe_b64encode(assr).decode("ascii").rstrip("=")
    isr = handler.settings["image_server"]
    signed = f"{isr}/s/ci/{fspec}/-{first}/{assr}.{ext}"

    base[key] = signed
    return signed


@export
def sign_object(handler, key, suffix):
    try:
        base = handler._reified_tags
    except AttributeError:
        handler._reified_tags = base = {}

    if key in base:
        return base[key]

    assr = hmac.new(get_as_secret(), key.encode("utf8"), hashlib.sha224).digest()[:10]
    assr = base64.urlsafe_b64encode(assr).decode("ascii").rstrip("=")
    isr = handler.settings["image_server"]
    signed = f"{isr}/{key}/{assr}.{suffix}"

    base[key] = signed
    return signed


@export
def gridify(handler, itera, per_row):
    if len(itera) <= per_row:
        yield itera
        return

    start = 0
    while 1:
        group = itera[start : start + per_row]
        if not group:
            break
        yield group
        start = start + per_row
