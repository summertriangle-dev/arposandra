#!/bin/bash

# Note: These cron scripts run with the working directory of start.sh, not in cron/

SERVERS="jp en"

function debug() {
    test '!' -z "${AS_CRON_DEBUG}" && echo $@ || return 0
}

function quiet_flag() {
    test -z "${AS_CRON_DEBUG}" && echo "--quiet" || return 0
}

function webhook() {
    if [[ -f /run/secrets/webhook_config ]]; then
        # like https://discordapp.com/api/webhooks/_id_/_token_ , nothing else
        local WEBHOOK_URL=$(cat /run/secrets/webhook_config)
        local MESSAGE="($1) All Stars master version changed to \`$2\`."
        local JSON="{\"content\": \"$MESSAGE\"}"
        ./sendmsg.py "$WEBHOOK_URL" "application/json" "$JSON" 
    fi
}

function update_server() {
    local SID=$1
    local CUR=$(python3 -m astool "${SID}" current_master)
    if [[ ! $? -eq 0 ]]; then
        CUR=""
    fi
    local QUIET_FLAG=$(quiet_flag)

    debug "@${SID} phase: dl_master"
    python3 -m astool "${SID}" "${QUIET_FLAG}" dl_master
    local NEW=$(python3 -m astool "${SID}" current_master)

    local PSPIPE=$(mktemp -t -u "psync_signal_fd.${SID}.XXXXXXXX")
    mkfifo "$PSPIPE"
    trap "rm -f ${PSPIPE}" EXIT

    if [[ "$SID" == "jp" ]]; then
        debug "@${SID} phase: pkgsync"
        python3 -m astool "${SID}" "${QUIET_FLAG}" pkg_sync --signal-cts="${PSPIPE}" main card:% &
    else
        debug "@${SID} phase: sync_region_banners"
        python3 -m astool_extra.sync_region_banners "${QUIET_FLAG}" -r ${SID} -l ${SID} --signal-cts="${PSPIPE}" &
    fi

    # wait for input on the signal pipe from pkgsync
    debug "@${SID} waiting for signal"
    IFS='' read -t 10 _ < "${PSPIPE}"
    debug "@${SID} signal received, continuing"

    debug "@${SID} phase: news"
    # This may conflict with the callout to sign asset urls.
    python3 news/get_news.py "${SID}"

    # Mtrack needs to run after news is settled
    debug "@${SID} phase: mtrack"
    if [[ "$CUR" != "$NEW" ]]; then
        python3 mtrack/mtrack.py "${QUIET_FLAG}" "${SID}" "${NEW}"
    else
        python3 mtrack/mtrack.py "${QUIET_FLAG}" "${SID}" -
    fi

    wait
    debug "@${SID} phase: all children exited"
    if [[ "$CUR" != "$NEW" ]]; then
        webhook "$SID" "$NEW"
        return 55
    fi
}

PIDS=""
for JOB in $@; do 
    debug "Start job: $JOB"
    update_server "$JOB" &
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

debug "exit status: $STATUS"
wait
exit $STATUS
