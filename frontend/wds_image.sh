#!/bin/sh
set -e

yarn install

# The container runs both sass and wds processes concurrently. We want to
# shut the container down if either process crashes/exits, and wait -n doesn't
# exist in the alpine shell, so we:
# - Spawn a canary subprocess whose pid is known to the subshells running
#   sass/wds.
# - Each subprocess kills the canary on the way out.
# - The main shell waits for the canary and exits when it dies.
canary() {
    while [[ true ]]; do
        sleep 1000
    done
}

canary &
CANARYPID=$!

CONTENT_BASE="/usr/fe/css_cache"

# Compile the CSS to the new temp dir (because node-sass --watch won't do it
# until the file is first modified)
yarn run node-sass --output $CONTENT_BASE/static/css css/theme-dark.scss &
yarn run node-sass --output $CONTENT_BASE/static/css css/theme-light.scss &

# Needed so if yarn exits non-zero it still kills the canary
set +e
(NODE_ENV=development yarn run webpack-dev-server --mode=development --static-directory=$CONTENT_BASE ; \
    kill $CANARYPID) &
JS_WATCH_PID=$!

(yarn run node-sass --watch --output $CONTENT_BASE/static/css css ; \
    kill $CANARYPID) &
CSS_WATCH_PID=$!

finish() {
    kill $CSS_WATCH_PID || true
    kill $JS_WATCH_PID || true
    exit 1
}

set -e
# For if the main shell is interrupted (docker stop, etc)
trap finish INT TERM

echo "Now interruptible" >&2
wait $CANARYPID
finish
