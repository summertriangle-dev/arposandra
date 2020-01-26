## Asset Server (Skyfarer)

**If you are just hacking on the web portion of the app, you can
skip this section.**

Skyfarer can serve decrypted images on the fly from the
package cache using hwdecrypt and the asset database. To prevent unnecessary
resource usage, requests need to be accompanied by a valid HMAC. 

### Setting Up the Cache

*Note: this section assumes you have a working astool setup.*

Follow the steps in ["Bootstrapping from zero"](https://howler.kirara.ca/services/astool#bootstrapping-from-zero)
to set up the cache. You can update the cache by running the `sync-cache` and `sync-cache-full`
commands from the utils image -- or manually with package_list_tool.

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