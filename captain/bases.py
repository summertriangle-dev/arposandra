import traceback

from tornado.web import HTTPError, RequestHandler


class BaseHTMLHandler(RequestHandler):
    def write_error(self, status_code, **kwargs):
        args = {"code": status_code, "message": self._reason}
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            args["traceback"] = "".join(traceback.format_exception(*kwargs["exc_info"]))

        self.render("error.html", **args)


class BaseAPIHandler(RequestHandler):
    pass


class DefaultHandler(BaseHTMLHandler):
    def prepare(self):
        raise HTTPError(404)
