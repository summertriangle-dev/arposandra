#!/bin/bash

function debug() {
    test -z "${AS_CRON_DEBUG}" && echo $@
}

PIDS=""
for JOB in $@; do 
    debug "Start job: $JOB"
    python3 border/border.py "$JOB" &
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
