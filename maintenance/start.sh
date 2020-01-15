#!/bin/sh

export PYTHONPATH=./lib:/usr/kars:$PYTHONPATH
executable=$1; shift

case $executable in
    news)
        exec python3 news/get_news.py $@
        ;;
    reparse)
        exec python3 news/reparse_news.py $@
        ;;
    sync-master) # ... sync-master [rgn] [karstool args...]
        SERVER=$1; shift
        exec python3 lib/karstool.py -r ${SERVER} $@ 
        ;;
    sync-cache)
        SERVER=$1; shift
        exec python3 lib/package_list_tool.py -r ${SERVER} $@ sync main card:%
        ;;
    sync-cache-full)
        SERVER=$1; shift
        exec python3 lib/package_list_tool.py -r ${SERVER} $@ sync everything
        ;;
    sync-both)
        SERVER=$1; shift
        python3 lib/karstool.py -r ${SERVER} && \
            python3 lib/package_list_tool.py -r ${SERVER} sync main card:%
        ;;
    plt)
        exec python3 lib/package_list_tool.py $@
        ;;
    mtrack) 
        exec python3 mtrack/mtrack.py $@
        ;;
    border-ingest)
        SERVER=$1; shift
        exec python3 border/border.py $SERVER $@
        ;;
    none)
        exit 0
        ;;
    *)
        echo "Unrecognized command: $@."
        exit 1
esac
