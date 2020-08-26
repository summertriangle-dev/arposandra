from tornado.web import RequestHandler, StaticFileHandler

from captain.dispatch import route, add_route
from captain import readonly_app_path

TEMPLATE_PATH = readonly_app_path("private", "sample", "templates")
STATIC_SETTINGS = {
    "static_url_prefix": "/custom/static/",
    "static_path": readonly_app_path("private/sample/static")
}

add_route(
    r"/custom/static/(.*)", StaticFileHandler, {"path": readonly_app_path("private/sample/static")},
)

class MyPrivateRequestHandlerBase(RequestHandler):
    def main_static_url(self, path: str, include_host: bool = None, **kwargs):
        return super().static_url(path, include_host, **kwargs)

    def static_url(self, path: str, **kwargs):
        return StaticFileHandler.make_static_url(STATIC_SETTINGS, path)

    def get_template_path(self):
        return TEMPLATE_PATH

@route(r"/sample/([0-9]+)")
class HelloWorldHandler(MyPrivateRequestHandlerBase):
    def get(self, member_id):
        member = self.settings["master"].lookup_member_by_id(member_id)

        tlbatch = member.get_tl_set()
        self._tlinject_base = self.settings["string_access"].lookup_strings(tlbatch)

        self.render("sample.html", name=member.name_romaji)
