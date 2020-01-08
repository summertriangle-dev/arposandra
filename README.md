# Arposandra

You need Python 3.6 to run this thing.
It's split into two apps, the asset server that produces images on demand
from the astool package cache, and the web server that produces the pages.

## Setting Up

I recommend using docker - (almost) ready-made configs are available in
the `variants` folder. Your docker-compose command will probably look like:

```
docker-compose -f docker-compose.yml \
    -f variants/config.dev-non-asset.yml \
    -f variants/config.postgres.yml [build/up etc...]
```

You will need to make the following edits to the configs:

- postgres: update both instances of `AS_POSTGRES_DSN` to point at the right 
  hostname. It's usually `xxxxx_db_1`, where xxxxx is the name of the folder you
  cloned this repo into (such as `arposandra`).
- dev-non-asset: Change `AS_IMAGE_SERVER` to point at the right hostname.
  Do not use a docker-internal host because your browser will request images
  from it.
- General: You should also change the mounts to point at the right directories
  on your computer. "./arena/astool_server_specific_fixme" should point
  to a folder containing the "masters" folder.
- Alternatively, just create the symlink "./arena/astool_server_specific_fixme"
  that points to the right place.

To make CSS work in dev mode, you need to compile the sass files (not in
docker):

```
cd frontend
yarn
make all
```

The frontend folder also has the `control.sh` script which will run 
webpack-dev-server and live sass for you. This makes it so

- JS works in dev mode, and
- Changes you make to sass files are automatically compiled.

**IMPORTANT**: If you want the utils image to build correctly, you need to follow
the instructions in `maintenance/README.md` to install astool. Otherwise,
**remove it from all configs**.

## Application Configuration

Configuration is done through these environment variables:
```bash
# Path to the astool data directory OR a master directory.
# It should be the directory where the astool memo or masterdata.db is.
AS_DATA_ROOT=/external/astool

# SSL is not supported - you should use nginx or server for that.
# See xxxxx for a sample nginx config file.
AS_WEB_ADDR=0.0.0.0
AS_WEB_PORT=30001

# Enables developer conveniences (tornado autoreload, disables template cache, t_reify, etc)
# THIS IS INSECURE - DO NOT LEAVE IT ENABLED IN PRODUCTION.
AS_DEV=1

# URL prefix for the asset server.
AS_IMAGE_SERVER: "http://10.252.52.102:5001"

# HMAC key for signing TLInject submissions. You will want to keep this
# fairly random.
AS_TLINJECT_SECRET=testing

# HMAC key for signing asset urls. You can set this to any random HEX string
# if you run web only.
AS_ASSET_JIT_SECRET="44BDF8618EAE4E6590161D37A80BB80E"

# Displayed in the footer.
AS_HOST_ID="Mari-Docker"

# DB connection parameters in URL form - You can also leave this undefined
# and use the PG* environment variables.
AS_POSTGRES_DSN="postgres://postgres:example@allstars_db_1/postgres"

# Exclusive to the asset server. You don't need them if you run web only.
AS_ASSET_ADDR=0.0.0.0
AS_ASSET_PORT=30001
```

~~You can point the image server at (insert public url here) if you're not
running an asset server~~. Unfortunately this doesn't work anymore because the 
URLs changed. 

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

The Makefile in frontend/ is wired up to run watch commands to compile
the sass and js code. You can use the control.sh script to run both in
the same window.

```bash
cd frontend
./control.sh
```

When you are ready to commit your changes, run `make all` to ensure
all files are up-to-date.

## Localization

Translations exist in two places.

- The Python code uses the files in the `ui_strings` directory. To create
  a new language, duplicate en.po to the new language code, then translate
  it. cd into the `ui_strings` directory and type `make` to build the new
  string files.
- The frontend has its own translations in `frontend/js/lang`. To translate
  it, duplicate the en.js file, and translate it. Webpack should pick it
  up automatically. **Important: the JS code only loads languages that
  have a Python counterpart.**

## Asset Server

This section has been moved to skyfarer/README.md.
