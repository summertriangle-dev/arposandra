#!/bin/sh

fail() {
    >&2 echo "$@"
    exit 1
}

if [[ "$ASTOOL_STORAGE" == "" ]]; then
    fail "You forgot to set ASTOOL_STORAGE in the environment."
fi

if [[ "$AS_POSTGRES_DSN" == "" ]]; then
    fail "You forgot to set AS_POSTGRES_DSN in the environment."
fi

set -e

CANON_V=$(python -m astool jp current_master)
TRANS_V=$(python -m astool en current_master)
ASM="$ASTOOL_STORAGE/jp/masters/${CANON_V}"

echo "Building base index: EN"
python -m captain.script.create_search_criteria captain/static/search \
    en ${CANON_V} jp -t ${TRANS_V} -s en
echo "Building used skill index: EN"
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums card_index_v1__skills \
    captain/static/search/card.skills.enum.en.json
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums accessory_index_v1__skills \
    captain/static/search/accessory.skills.enum.en.json
echo "Building base index: JA"
python -m captain.script.create_search_criteria captain/static/search \
    ja ${CANON_V} jp
echo "Building used skill index: JA"
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums card_index_v1__skills \
    captain/static/search/card.skills.enum.ja.json
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums accessory_index_v1__skills \
    captain/static/search/accessory.skills.enum.ja.json