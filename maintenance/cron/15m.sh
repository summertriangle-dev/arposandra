#!/bin/bash

function debug() {
    test '!' -z "${AS_CRON_DEBUG}" && echo $@ || return 0
}

function quiet_flag() {
    test -z "${AS_CRON_DEBUG}" && echo "--quiet" || return 0
}

PIDS=""
for JOB in $@; do 
    debug "Start job: $JOB"
    python3 border/border.py $(quiet_flag) "$JOB" &
    PIDS="${PIDS} $!"
    debug $PIDS
done

STATUS=0
for PID in $PIDS; do 
    wait $PID; stat="$?"
    if [[ ! $stat -eq 0 ]]; then
        STATUS=$stat
    fi
done

wait
exit $STATUS
