#!/bin/sh
set -e

export PYTHONPATH=/usr/kars:./lib:$PYTHONPATH
executable=$1; shift

help() {
    echo "Welcome to the maintenance image, version 0.2.0."
    echo "Refer to maintenance/start.sh for the available commands."
    echo "You can also drop to a shell with the 'sh' command."
}

case $executable in
    cron)
        JOBNAME=$1; shift
        if [[ -x "cron/${JOBNAME}.sh" && -f "cron/${JOBNAME}.sh" ]]; then
            exec "cron/${JOBNAME}.sh" "$@"
        else
            echo "job ${JOBNAME} doesn't exist"
            exit 1
        fi
        ;;
    ##### ADMIN COMMANDS #####
    astool)
        exec python3 -m astool "$@"
        ;;
    astool-extra-command)
        SUBCMD=$1; shift
        exec python3 -m "astool_extra.${SUBCMD}" "$@"
        ;;

    ##### DEBUG COMMANDS #####
    reparse-news)
        exec python3 news/reparse_news.py "$@"
        ;;
    add-fake-saint-data)
        exec python3 border/et_fake.py "$@"
        ;;
    sh)
        exec sh "$@"
        ;;

    become-host-for-cron-execs)
        sleep infinity
        ;;
    none)
        exit 0
        ;;
    *)
        help
        exit 1
        ;;
esac
