import json
import os
import time
from typing import Type, TypeVar, Optional, Callable, Iterable

import tornado.web
from tornado import locale

ROUTES = []
H = TypeVar("H", bound=tornado.web.RequestHandler)


def add_route(regex: str, handler: Type[H], inits: Optional[dict] = None):
    if inits:
        ROUTES.append((regex, handler, inits))
    else:
        ROUTES.append((regex, handler))


def route(*regexes: Iterable[str], **kwargs: dict) -> Callable[[Type[H]], Type[H]]:
    def wrapper(handler: Type[H]) -> Type[H]:
        for regex in regexes:
            if kwargs:
                ROUTES.append((regex, handler, kwargs))
            else:
                ROUTES.append((regex, handler))

        return handler

    return wrapper


class LanguageCookieMixin(tornado.web.RequestHandler):
    def get_user_locale(self):
        preferred_lang = self.get_cookie("lang", None)
        if preferred_lang not in locale.get_supported_locales():
            return None
        return locale.get(preferred_lang)

    def get_user_dict_preference(self):
        preferred_lang = self.get_cookie("mdic", None)
        if not preferred_lang:
            return self.locale.code.split("_")[0]
        return preferred_lang
