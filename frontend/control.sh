#!/bin/bash
set -e

make js-watch &
JS_WATCH_PID=$!

make sass-watch &
CSS_WATCH_PID=$!


finish() {
    kill -SIGINT $JS_WATCH_PID
    kill -SIGINT $CSS_WATCH_PID
}

echo "[-] sass: $CSS_WATCH_PID webpack: $JS_WATCH_PID"
trap finish EXIT

while read line; do
    true
done