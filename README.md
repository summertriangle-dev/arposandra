# Arposandra

You need Python 3.6 to run this thing.
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

If you want to run the tools in the utils image, you need to follow the instructions
to clone astool in the maintenance directory.

## Application Configuration

Configuration is done through [environment variables, which are described in the wiki](https://github.com/summertriangle-dev/arposandra/wiki/Configuration-Variables).

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
  a new language, duplicate en_tornado.po and en_static.po to the new 
  language code, then translate it. cd into the `ui_strings` directory
  and type `make` to build the new string files.
- To extract new strings, do `make genstrings`. To add them to the current 
  language files, run `make msgmerge`. You will then be able to update the
  individual translation files.
- The frontend has its own translations in `frontend/js/lang`. To translate
  it, duplicate the en.js file, and translate it. Webpack should pick it
  up automatically. **Important: the JS code only loads languages that
  have a Python counterpart.**

## Asset Server

This section has been moved to skyfarer/README.md.
