This is a collection of utilities meant for running as cron jobs, etc.
They are meant to run from a single docker image, so you can do something like

```bash
docker-compose -f docker-compose.yml -f ... run --rm utils [news|karstool|sync...]
```

**NOTE**: The image will not run properly without a copy of astool
in the astool/ directory. It's not needed for docker build, but if you
plan to run a prod instance of the site you may want to run:

`git clone https://howler.kirara.ca/services/astool.git astool`

For the list of commands, see start.sh.