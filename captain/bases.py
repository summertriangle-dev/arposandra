import traceback

from tornado.web import HTTPError, RequestHandler
from tornado import locale


class BaseAPIHandler(RequestHandler):
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


class BaseHTMLHandler(BaseAPIHandler):
    def write_error(self, status_code, **kwargs):
        args = {"code": status_code, "message": self._reason}
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            args["traceback"] = "".join(traceback.format_exception(*kwargs["exc_info"]))

        self.render("error.html", **args)

    def get_show_devtext(self):
        f = self.get_secure_cookie("cs_fflg_v2")
        if f is None:
            return False

        try:
            flag = int(f)
        except ValueError:
            flag = 0

        return flag & (1 << 1)


class DefaultHandler(BaseHTMLHandler):
    def prepare(self):
        raise HTTPError(404)
