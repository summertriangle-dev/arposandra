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
python -m captain.script.create_search_criteria captain/static/search/base.en.json \
    en ${CANON_V} jp -t ${TRANS_V} -s en
echo "Building used skill index: EN"
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums \
    captain/static/search/skills.enum.en.json
echo "Building base index: JA"
python -m captain.script.create_search_criteria captain/static/search/base.ja.json \
    ja ${CANON_V} jp
echo "Building used skill index: JA"
ASTOOL_MASTER=$ASM python -m captain.script.make_skill_enums \
    captain/static/search/skills.enum.ja.json
