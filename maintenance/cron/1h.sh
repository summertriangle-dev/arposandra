#!/bin/bash

# Note: These cron scripts run with the working directory of start.sh, not in cron/

SERVERS="jp en"

function webhook() {
    if [[ -f /run/secrets/webhook_config ]]; then
        # like https://discordapp.com/api/webhooks/_id_/_token_ , nothing else
        local WEBHOOK_URL=$(cat /run/secrets/webhook_config)
        local MESSAGE="($1) All Stars master version changed to \`$2\`."
        local JSON="{\"content\": \"$MESSAGE\"}"
        curl -q -d "$JSON" -H "Content-Type: application/json" "$WEBHOOK_URL"
    fi
}

function update_server() {
    local SID=$1
    local CUR=$(python3 -m astool "${SID}" current_master)
    if [[ ! $? -eq 0 ]]; then
        CUR=""
    fi

    if [[ "$SID" == "jp" ]]; then
        python3 -m astool "${SID}" --quiet dl_master
        python3 -m astool "${SID}" --quiet pkg_sync main card:% &
    else
        python3 -m astool "${SID}" --quiet dl_master
        python3 -m astool_extra.sync_region_banners -r ${SID} -l ${SID} --quiet &
    fi

    local NEW=$(python3 -m astool "${SID}" current_master)

    # Try this and see if it flakes
    python3 news/get_news.py "${SID}" &

    if [[ "$CUR" != "$NEW" ]]; then
        webhook "$SID" "$NEW"
        return 55
    fi
}

PIDS=""
for JOB in $@; do 
    update_server "$JOB" &
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