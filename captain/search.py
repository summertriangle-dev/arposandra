from tornado.web import RequestHandler
from tornado.locale import get_supported_locales

from .dispatch import route, LanguageCookieMixin
from . import pageutils
# FIXME: move to somewhere more official
from maintenance.mtrack.indexer import Schema, CardIndex
import libcard2.localization



@route(r"/api/private/search/bootstrap.json")
class APISearchBootstrap(RequestHandler):
    def get(self):
        return

@route(r"/api/private/search/cards.json")
class APISearchExecWithSchemaBase(RequestHandler):
    schema: Schema

    async def post(self):
        binds = {}

        for field in self.schema.fields:
            it = self.get_argument(field.name)
            if it is not None:
                binds[field.name] = it
        
        
