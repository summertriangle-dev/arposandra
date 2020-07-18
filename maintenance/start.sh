#!/bin/sh

export PYTHONPATH=/usr/kars:./lib:$PYTHONPATH
executable=$1; shift

case $executable in
    news)
        exec python3 news/get_news.py "$@"
        ;;
    reparse)
        exec python3 news/reparse_news.py "$@"
        ;;
    sync-master) # ... sync-master [rgn] [karstool args...]
        SERVER=$1; shift
        exec python3 -m astool "${SERVER}" --quiet dl_master
        ;;
    sync-cache)
        SERVER=$1; shift
        exec python3 -m astool "${SERVER}" --quiet pkg_sync main card:%
        ;;
    sync-cache-full)
        SERVER=$1; shift
        exec python3 -m astool "${SERVER}" --quiet pkg_sync everything
        ;;
    sync-both)
        SERVER=$1; shift
        python3 -m astool "${SERVER}" --quiet dl_master && \
            python3 -m astool "${SERVER}" --quiet pkg_sync main card:%
        ;;
    astool_command)
        exec python3 -m astool "$@"
        ;;
    mtrack)
        exec python3 mtrack/mtrack.py "$@"
        ;;
    border-ingest)
        SERVER=$1; shift
        exec python3 border/border.py "$SERVER" "$@"
        ;;
    border-ingest2)
        exec python3 border/et_fake.py "$@"
        ;;
    astool-extra-command)
        SUBCMD=$1; shift
        exec python3 -m "astool_extra.${SUBCMD}" "$@"
        ;;
    none)
        exit 0
        ;;
    *)
        echo "Unrecognized command: $1 $*."
        exit 1
esac
