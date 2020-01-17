import json
import os
import time

import tornado.web
from tornado import locale

ROUTES = []


def route_if(yes, reason, *regexes):
    if yes:
        return route(*regexes)
    else:
        print(reason)
        return lambda f: f


def route(*regexes):
    def wrapper(handler):
        for regex in regexes:
            ROUTES.append((regex, handler))
        return handler

    return wrapper


def dev_mode_only(wrapped):
    if os.environ.get("AS_DEVELOPMENT", ""):
        return wrapped

    class not_dev_error(tornado.web.RequestHandler):
        def get(self, *args):
            self.set_status(400)
            self.set_header("Content-Type", "text/plain; charset=utf-8")
            self.write("The requested endpoint is only available in development mode.")

    return not_dev_error


class LanguageCookieMixin(tornado.web.RequestHandler):
    def get_user_locale(self):
        preferred_lang = self.get_cookie("lang", None)
        if preferred_lang not in locale.get_supported_locales():
            return None
        return locale.get(preferred_lang)
