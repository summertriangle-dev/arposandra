# Arposandra

You need Python 3.9 to run this thing.
It's split into two apps, the asset server that produces images on demand
from the astool package cache, and the web server that produces the pages.

## Setting Up

I recommend using docker - (almost) ready-made configs are available in
the `variants` folder. Your docker-compose command will probably look like:

```
docker-compose -f docker-compose.yml \
    -f variants/config.dev.yml \
    -f variants/config.postgres.yml [build/up etc...]
```

You will need to make the following edits to the configs:

- postgres: update both instances of `AS_POSTGRES_DSN` to point at the right 
  hostname. It's usually `xxxxx_db_1`, where xxxxx is the name of the folder you
  cloned this repo into (such as `arposandra`).
- dev: Change `AS_IMAGE_SERVER` to point at the right hostname.
  Do not use a docker-internal host because your browser will request images
  from it.
- General: You should also change the mounts to point at the right directories
  on your computer. "./arena/astool_server_specific_fixme" should point
  to a folder containing the "masters" folder.
- Alternatively, just create the symlink "./arena/astool_server_specific_fixme"
  that points to the right place.

If you want to run the tools in the utils image, you need to follow the instructions
to clone astool in the maintenance directory.

## Application Configuration

See `doc/config.md`.

## Adding New Pages

The web app code lives in the captain directory. The basic flow to add a new page
is like this:

1. Decide whether the page should go in a new py file. Pages that are similar
   in function should share a file.
   - If you make a new file, you need to import it in `captain/__init__.py`.
2. Create the RequestHandler subclass. Please look at the Tornado docs to
   see what you can do here.
3. Use the `dispatch.route` decorator to add URLs to your page. Example:
   ```python
   from tornado.web import RequestHandler
   from .dispatch import route
   @route(r"/mypage/([0-9]+)")
   class SomePage(RequestHandler):
       def get(self, param):
           self.write(f"Hello world! Your number was {param}.")
   ```

## Frontend code (Sass and JS)

The CSS and Javascript code is in frontend/. Starting the js-dev docker container
(defined in variants/config.dev.yml) will set up webpack-dev-server for you.
No need to do anything on the host side anymore.

Remember to change the AS_WDS_HOST environment variable in config.dev.yml to
either localhost, or an accessible host if testing on other devices.

## Localization

See `doc/localization.md`.

## Asset Server

This section has been moved to skyfarer/README.md.
