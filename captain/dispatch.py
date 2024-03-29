import json
import os
import time
from typing import Type, TypeVar, Optional, Callable, Iterable, List, Union, Tuple, cast

import tornado.web
from tornado import locale

from libcard2.master import MasterData
from .database import DatabaseCoordinator

H = TypeVar("H", bound=tornado.web.RequestHandler)
RouteDef = Union[Tuple[str, H, dict], Tuple[str, H]]

ROUTES: List[RouteDef] = []


def add_route(regex: str, handler: Type[H], inits: Optional[dict] = None):
    if inits:
        ROUTES.append((regex, handler, inits))
    else:
        ROUTES.append((regex, handler))


def route(*regexes: str, **kwargs: dict) -> Callable[[Type[H]], Type[H]]:
    def wrapper(handler: Type[H]) -> Type[H]:
        for regex in regexes:
            if kwargs:
                ROUTES.append((regex, handler, kwargs))
            else:
                ROUTES.append((regex, handler))

        return handler

    return wrapper


class DatabaseMixin(object):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if tornado.web.RequestHandler not in cls.__mro__:
            raise TypeError("This mixin needs to be used with a subclass of RequestHandler.")

    def master(self) -> MasterData:
        return cast(tornado.web.RequestHandler, self).settings["master"]

    def database(self) -> DatabaseCoordinator:
        return cast(tornado.web.RequestHandler, self).settings["db_coordinator"]
