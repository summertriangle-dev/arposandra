## Asset Server (Skyfarer)

**If you are just hacking on the web portion of the app, you can
skip this section.**

Skyfarer can serve decrypted images on the fly from the
package cache using hwdecrypt and the asset database. To prevent unnecessary
resource usage, requests need to be accompanied by a valid HMAC. 

### Setting Up the Cache

Note: This section is copypasted directly from the astool documentation. Refer to it
for details on what the commands do. 

Note 2: astool is now available standalone! Get it at
https://howler.kirara.ca/services/astool.git

Skyfarer, of course, requires assets to work. We currently need the
`main` and `card:...` packages for the app to have all needed images. 

astool and co. are used to maintain the cache:

```bash
# Virtualenv setup, etc.
# Note: You should re-use the app server's virtualenv here. No need to create another.
python3 -m venv rt
source rt/bin/activate
pip install -r requirements.txt
export ASTOOL_STORAGE=/mnt/storage/as-cache/data
export LIVE_MASTER_CHECK_ALLOWED=1

python3 astool.py bootstrap
# Get master
python3 karstool.py
# Initial download (>1GB!)
python3 package_list_tool.py main 'card:%'
```

After bootstrapping, you can update the master using karstool:
```bash
# Activate the virtualenv first.
LIVE_MASTER_CHECK_ALLOWED=1 python3 karstool.py
```

And you can download any new assets too:
```bash
# Activate the virtualenv first.
# Validate (download) the "main" package, and all packages starting with card:.
python3 package_list_tool.py main 'card:%'
```

### Proxying the Asset Server

You should put a caching proxy in front of skyfarer for production deployments.
Below is the nginx config I use, you will need to adapt it for your server.

```
server {
    include conf.d/listen443.in;
    server_name tirofinale.kirara.ca;

    # CloudFlare generic config
    include conf.d/cfssl.in;
    include conf.d/cloudflare.in;

    root /dev/null;

    location / {
        proxy_cache_key "$scheme$proxy_host$uri";
        proxy_cache generic_zone;
        proxy_cache_valid 30d;
        proxy_cache_use_stale error timeout invalid_header updating;
        proxy_cache_background_update on;
        add_header X-Skyfarer-Cache $upstream_cache_status;

        proxy_set_header "X-Real-IP" $remote_addr;
        proxy_set_header "X-Scheme" $scheme;
        proxy_pass http://127.2.0.1:33002;
    }
}
```