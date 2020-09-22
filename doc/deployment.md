# Deployment

This is a description of the production environment. It is not intended as 
a guide, but you may find inspiration from it for your own deployment.

## Submodules

| Module name | Where | Source |
|=============|=======|========|
| astool | maintenance/lib | hxxps://howler.kirara.ca/services/astool |
| caveslime | captain/private/caveslime | hxxps://howler.kirara.ca/services/arposandra-plugin-caveslime |
| N/A | vendor/newrelic_asyncpg | TODO: patched version just floating in code dir |

To access Howler, first get a MIRAITICKET account then ask me to give you the
gitea entitlement. Assuming we already have a working relationship, of course.

## App servers

This is what our compose file looks like (variants/config.production.yml):

```yaml
version: '3.3'
services:
  asset:
    ports:
      - "127.2.0.1:33002:30001"
    volumes:
      - /mnt/storage/as-cache/data:/external/astool_storage:ro
      - /srv/apps/allstars/newrelic:/newrelic:ro
    environment:
      AS_ASSET_JIT_SECRET: # redacted
      AS_CANONICAL_REGION: "jp:ja"
      # Omit this env to disable the new relic agent.
      NEW_RELIC_CONFIG_FILE: "/newrelic/skyfarer.ini"
      NEW_RELIC_ENVIRONMENT: "production"
      AS_EXTRA_REGIONS: "en:en"
    restart: unless-stopped
  web:
    ports:
      - "127.2.0.1:33001:30001"
    volumes:
      - /mnt/storage/as-cache/data:/external/astool_storage:ro
      - /srv/apps/allstars/newrelic:/newrelic:ro
    environment:
      AS_IMAGE_SERVER: "https://tirofinale.kirara.ca"
      AS_TLINJECT_SECRET: # redacted
      AS_ASSET_JIT_SECRET: # redacted
      AS_HOST_ID: queenofpurple-docker
      AS_POSTGRES_DSN: "postgres://[redacted]:[redacted]@[redacted]/allstars"
      AS_CANONICAL_REGION: "jp:ja"
      AS_EXTRA_DICTIONARIES: "en:en:Official Translations;en:ko:Official Translations;en:th:Official Translations;en:zh:Official Translations"
      AS_COOKIE_SECRET: # redacted
      AS_FEEDBACK_URL: "https://docs.google.com/forms/d/e/1FAIpQLSenCysEe8LjLm0Obq-rWPlH1j-sB5C30U2B78ngDP-7LcUyqw/viewform?usp=sf_link"
      # Omit this env to disable the new relic agent.
      NEW_RELIC_CONFIG_FILE: "/newrelic/captain.ini"
      NEW_RELIC_ENVIRONMENT: "production"
    restart: unless-stopped
  utils:
    # Note: this is the same uid as the 'allstars' user on the host
    # This is done to share ownership of astool's cache.
    user: "123"
    secrets:
      - webhook_config
    volumes:
      - /mnt/storage/as-cache/data:/external/astool_storage
      - # redacted - see DESTINYGUNDAM readme for why this is here
    environment:
      AS_ASSET_JIT_SECRET: # redacted
      AS_POSTGRES_DSN: "postgres://[redacted]:[redacted]@[redacted]/allstars"

secrets:
  webhook_config:
    file: variants/webhook_url_prod.txt
```

## Nginx

The nginx configuration looks like this (the one in skyfarer's readme is
outdated somewhat):

```nginx
server {
    listen 80 default_server;
    server_name allstars.kirara.ca tirofinale.kirara.ca;
    rewrite ^ https://$host$request_uri permanent;
}

server {
    listen 443 ssl http2;
    server_name tirofinale.kirara.ca;

    include cloudflaressl.conf;
    include cloudflare.conf;

    root /dev/null;

    # Optional sections for DESTINYGUNDAM redacted. See readme for what goes here.

    location / {
        proxy_cache_key "$scheme$proxy_host$uri";
        proxy_cache generic_zone;
        proxy_cache_valid 30d;
        proxy_cache_use_stale error timeout invalid_header updating;
        proxy_cache_background_update on;
        add_header X-Skyfarer-Cache $upstream_cache_status;

        proxy_set_header "X-Real-IP" $http_cf_connecting_ip;
        proxy_set_header "X-Scheme" $scheme;
        proxy_pass http://127.2.0.1:33002;
    }
}

server {
    listen 443 default_server ssl http2;
    server_name allstars.kirara.ca;

    # Sets up TLS params for Cloudflare SSL (we use strict mode with an origin cert), and a "modern" config from mozilla's config generator
    include cloudflaressl.conf;
    # Sets up allow/block lists for Cloudflare's IPs.
    include cloudflare.conf;

    root /dev/null;

    error_page 500 502 503 504 /allstars_5xx.html;
    location = /allstars_5xx.html {
        root /srv/www/error_pages;
    }

    location / {
        add_header Content-Security-Policy "default-src 'self'; connect-src https://tirofinale.kirara.ca https://a-rise.kirara.ca 'self'; img-src https://tirofinale.kirara.ca https: blob: 'self'; style-src 'self' 'unsafe-inline'; script-src https://a-rise.kirara.ca 'self'";
        proxy_set_header "X-Real-IP" $http_cf_connecting_ip;
        proxy_set_header "X-Scheme" $scheme;
        proxy_pass http://127.2.0.1:33001;
    }

    # Caching for skill tree lookups, which can be slow
    location ~ /api/v1/([a-f0-9]+)/skill_tree/(.+).json {
        proxy_cache_key "tt_v1:$1:$2";
        proxy_cache as_tt_zone;
        proxy_cache_valid 7d;
        add_header X-Captain-Cache $upstream_cache_status;

        proxy_set_header "X-Real-IP" $http_cf_connecting_ip;
        proxy_set_header "X-Scheme" $scheme;
        proxy_pass http://127.2.0.1:33001;
    }

    # Note: Next two sections optional for make_api script below - feel free to omit
    location = /api/v1/master_version.json {
        root /srv/apps/allstars/public_html;
        add_header "Cache-Control" "no-cache";
    }

    location /api/plumbing {
        root /srv/apps/allstars/public_html;
        add_header "Cache-Control" "no-cache";
    }
}
```

## Maintenance

Scripts in the maintenance/ folder can be run periodically to update parts
of the site. Here's a list of what features require which:

- Event tracker: `border` <sup>1</sup>
- Schedule: `news`, `mtrack`
- Card sets: `mtrack`
- In-game news: `news`
- CaveSlime: `mde`
- `mtrack` script: `news`

<sup>1</sup>: `mtrack` is recommended as it will allow displaying event cards
and banner on the tracker page.

All the scripts require astool to be configured.

### Cron scripts

We use the prewritten scripts in maintenance/cron/ to run all the scripts,
which are invoked like this:

```bash
/usr/local/bin/docker-compose -f docker-compose.yml -f variants/config.production.yml \
    exec -T utils './start.sh' cron 1h jp en
```

assuming you have a utils container already running (the default action 
for docker-compose up does this), or:

```bash
/usr/local/bin/docker-compose -f docker-compose.yml -f variants/config.production.yml \
    run --rm utils cron 1h jp en
```

which will spin up a temporary container.

The actual cron script running on the host looks like this:

```bash
#!/bin/bash
cd ~
export LIVE_MASTER_CHECK_ALLOWED=1
export ASTOOL_STORAGE=/mnt/storage/as-cache/data

APP_CODE_DIR="arposandra"
DOCKER_COMPOSE="/usr/local/bin/docker-compose -f docker-compose.yml -f variants/config.production.yml"

# TODO: Move into docker container
function resolve_bndl_version() {
    echo $(source rt/bin/activate && cd arposandra/maintenance/lib && python3 -m astool $1 resolve)
}

pushd $APP_CODE_DIR >> /dev/null
$DOCKER_COMPOSE exec -T utils './start.sh' cron 1h jp en
EXITSTAT=$?
popd >> /dev/null

if [[ ! $EXITSTAT -eq '0' ]]; then
    python3 ~/plumbing/make_api.py jp $(resolve_bndl_version jp)
    python3 ~/plumbing/make_api.py en $(resolve_bndl_version en)

    pushd $APP_CODE_DIR >> /dev/null
    $DOCKER_COMPOSE stop web asset
    $DOCKER_COMPOSE start web asset
    popd >> /dev/null
fi
```

make_api.py (not required at all - just a leftover from ancient times):

```python
import os
import json
import time
import sys

region = sys.argv[1]
bundle = sys.argv[2]

api_directory = os.path.join(os.getenv("HOME"), "public_html", "api", "plumbing", region)
os.makedirs(api_directory, exist_ok=True)

with open(os.path.join(os.getenv("ASTOOL_STORAGE"), region, "astool_store.json"), "r") as memo:
    di = json.load(memo)

with open(os.path.join(api_directory, "master_version.json"), "w") as api:
    json.dump({
        "version": di["master_version"],
        "update_time": int(time.time()),
        "update_platform": "iphoneos",
        "bundle_version": bundle,
    }, api)
```

The 15-minute job is much simpler:

```bash
#!/bin/bash

cd ~
APP_CODE_DIR="arposandra"
DOCKER_COMPOSE="/usr/local/bin/docker-compose -f docker-compose.yml -f variants/config.production.yml"

pushd $APP_CODE_DIR >> /dev/null
$DOCKER_COMPOSE exec -T utils './start.sh' cron 15m jp en
popd >> /dev/null
```

### Even more??

DESTINYGUNDAM also "needs" to be run when new cards are added, but currently
isn't hooked up to a cron job or even source tracked. We should really get on that.
