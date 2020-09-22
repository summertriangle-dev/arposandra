For app localizations, you need to look in two places.

## Server-side

The Python code uses the files in the `ui_strings` directory. To create a new 
language:

- First duplicate en_tornado.po and en_static.po to the new language code
  (e.g. fr_tornado.po)
- Translate the file. Generally you don't want to touch any lines starting with
  "msgid". The lines with "msgstr" contain the content to be translated.
- Type `make msgfmt` in the ui_strings dir to rebuild the language files.
  Then restart to see the new strings.

To update the languages after adding some new strings:

- Do `make genstrings` in ui_strings dir.
- Then `make msgmerge` to update the translation files with the new strings
  from the template.
- Update the indivdual language files.
- Type `make msgfmt` in the ui_strings dir to rebuild the language files.


## JS-side

The frontend has its own translations in `frontend/js/lang`. To translate 
it, duplicate the en.js file, and translate it. Webpack should pick it up 
automatically. **Important: the JS code only loads languages that have a 
Python counterpart.**
