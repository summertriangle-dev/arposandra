#!/bin/bash

PIDS=""
for JOB in $@; do 
    python3 border/border.py "$JOB" &
    PIDS="${PIDS} $!"
done

STATUS=0
for PID in $PIDS; do 
    wait $PID; stat="$?"
    if [[ ! $stat -eq 0 ]]; then
        STATUS=$stat
    fi
done

exit $STATUS