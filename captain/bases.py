import traceback

from tornado.web import HTTPError, RequestHandler
from tornado import locale


class BaseAPIHandler(RequestHandler):
    def get_user_locale(self):
        preferred_lang = self.get_cookie("lang", None)
        if preferred_lang not in locale.get_supported_locales():
            return None
        return locale.get(preferred_lang)

    def get_browser_locale(self, default: str = "en_US"):
        return locale.get(default)

    # from tornado source
    def get_accept_language(self):
        if "Accept-Language" in self.request.headers:
            languages = self.request.headers["Accept-Language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].strip().startswith("q="):
                    try:
                        score = float(parts[1].strip()[2:])
                        if score < 0:
                            raise ValueError()
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                if score > 0:
                    locales.append((parts[0], score))

            if locales:
                locales.sort(key=lambda pair: pair[1], reverse=True)
                codes = [loc[0] for loc in locales]
                return codes

        return []

    def get_user_dict_preference(self):
        aggregator = self.settings["string_access"]
        all_dicts = [aggregator.master.language, *(aggregator.choices.keys())]

        for code in self.get_accept_language():
            match_code = code.split("-")[0]
            if match_code in all_dicts:
                return match_code

        return aggregator.master.language


class BaseHTMLHandler(BaseAPIHandler):
    def write_error(self, status_code, **kwargs):
        args = {"code": status_code, "message": self._reason}
        if self.settings.get("serve_traceback") and "exc_info" in kwargs:
            args["traceback"] = "".join(traceback.format_exception(*kwargs["exc_info"]))

        self.render("error.html", **args)

    def get_user_dict_preference(self):
        preferred_lang = self.get_cookie("mdic", None)
        if not preferred_lang:
            preferred_lang = super().get_user_dict_preference()

        return preferred_lang

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
