This is a collection of utilities meant for running as cron jobs, etc.
They are meant to run from a single docker image, so you can do something like

```bash
docker-compose -f docker-compose.yml -f ... run --rm utils [news|karstool|sync...]
```

**NOTE**: The image will not function without
astool/IceAPI copied into the `lib` folder. You can get the required files from
Howler (git@wireguard.kirara.ca:services/astool.git).

Supported commands:

- `news` - Fetch in-game news.
- `reparse` - Re-run the DM parser on already fetched news. Doesn't rely
  on external services.
- `sync-master` - Same as running karstool from the astool distribution, but
  in docker!
- `sync-cache` - Same as running package_list_tool on main and card:* packages
- `plt` - Trap door for running package_list_tool with arbitrary args.

For a full list, see start.sh.