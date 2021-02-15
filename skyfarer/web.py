import os
import binascii
import hmac
import hashlib
import base64
import imghdr
import logging
import json

from tornado.web import Application, RequestHandler
from tornado.iostream import StreamClosedError

from libcard2.utils import from_frame_info
from .extract import ExtractContext, ExtractFailure
from . import adv_script_parser

# from .inspect_backend import InspectState


def _test_for_ffd8(h, f):
    if h[0:2] == b"\xff\xd8":
        return "jpeg"


if _test_for_ffd8 not in imghdr.tests:
    imghdr.tests.append(_test_for_ffd8)


def application(master, language, extras, debug):
    application = AssetServerApplication(
        master,
        language,
        extras,
        [
            (r"/i(?:/([a-z]+))?/([^/]+)/([^/\.]+)(?:\.(?:png|jpg))?", ReifyHandler),
            (
                # The 3 letters encode the type of frame and icons the image should have.
                # See libcard2/utils.py for the definitions.
                # Replace a letter with z, y, or x depending on position to omit
                # that element.
                r"/s/ci/([sgrz][vpuky][mpcanex])/([^/]+)/([^/]+)\.(jpg|png)",
                SyntheticCardIconHandler,
            ),
            (r"/adv/(.+)/([^/\.]+)\.json", AdvScriptHandler),
            (r"/advg/(.+)/([0-9]+)\.(?:png|jpg)", AdvScriptGraphicHandler),
            (r"/if(?:/([a-z]+))?/(.+)/([^/\.]+)(?:\.(?:png|jpg))?", BareReifyHandler),
            (r"/thumb/([0-9]+)(w|h)/([^/]+)/([^/\.]+)\.(png|jpg)", SyntheticCardResizeHandler),
        ],
        debug=debug,
        disable_security=debug,
    )
    return application


class AssetServerApplication(Application):
    def __init__(self, masters, language, extras, *args, **kwargs):
        super().__init__(*args, **kwargs)

        master = os.path.join(masters, f"asset_i_{language}.db")
        cache = os.path.join(masters, "..", "..", "cache")
        secret = binascii.unhexlify(os.environ.get("AS_ASSET_JIT_SECRET"))

        if not all((master, cache)):
            raise ValueError("Configuration incomplete")

        contexts = {"": ExtractContext(master, cache)}
        contexts.update(
            {
                k: ExtractContext(
                    os.path.join(root, f"asset_i_{lang}.db"),
                    os.path.join(root, "..", "..", "cache"),
                )
                for k, (root, lang) in extras.items()
            }
        )

        primary_tag = os.environ.get("AS_CANONICAL_REGION", "jp:ja").split(":", 1)[0]
        contexts[primary_tag] = contexts[""]

        self.settings["extract_contexts"] = contexts
        self.settings["jit_secret"] = secret
        # self.settings["inspect_context"] = InspectState(masters, cache, storage)

    def change_asset_db(self, newdb):
        self.settings["extract_contexts"][""].change_asset_db(newdb)


######################################################
# HANDLERS
######################################################

ERR_REQUEST_NOAUTH = "Your request was declined because it was not properly authenticated."
ERR_REQUEST_NO_REGION = "Resources from this region are not available."


class BareReifyHandler(RequestHandler):
    def compute_etag(self):
        return None

    async def get(self, region, key, assr):
        my = hmac.new(self.settings["jit_secret"], key.encode("utf8"), hashlib.sha224).digest()

        try:
            assr = base64.urlsafe_b64decode(assr + "====")
        except ValueError:
            self.set_status(400)
            self.write(ERR_REQUEST_NOAUTH)
            return

        if not hmac.compare_digest(my[:10], assr):
            if not self.settings["disable_security"]:
                self.set_status(403)
                self.write(ERR_REQUEST_NOAUTH)
                return

        ec = self.settings["extract_contexts"].get(region or "")
        if not ec:
            self.set_status(404)
            self.write(ERR_REQUEST_NO_REGION)
            return

        did_headers = False
        buf = bytearray(65536)

        try:
            file_gen = ec.get_texture(key, buf)
            file_info = next(file_gen)
            etag = hashlib.sha224(file_info["file_id"].encode("utf8")).hexdigest()[:32]
            self.set_header("Etag", f'W/"{etag}"')

            if self.check_etag_header():
                self.set_status(304)
                return

            for buf, size in file_gen:
                if not did_headers:
                    img_type = imghdr.what(None, buf)
                    if img_type:
                        self.set_header("Content-Type", f"image/{img_type}")
                    did_headers = True
                self.write(bytes(buf[:size]))
                await self.flush()
        except ExtractFailure as e:
            if e.reason == 1:
                self.set_status(404)
                self.write(str(e))
                return
            else:
                self.set_status(503)
                self.write(str(e))
                return


class ReifyHandler(BareReifyHandler):
    async def get(self, region, key, assr):
        try:
            if key.startswith("-"):
                key = base64.urlsafe_b64decode("".join((key[1:], "===="))).decode("utf8")
            else:
                key = binascii.unhexlify(key).decode("utf8")
        except ValueError:
            self.set_status(400)
            return

        await super().get(region, key, assr)


class BaseAssrValidating(RequestHandler):
    def validate_assr(self, value, given):
        if self.settings["disable_security"]:
            return True

        my = hmac.new(self.settings["jit_secret"], value.encode("utf8"), hashlib.sha224).digest()

        try:
            given = base64.urlsafe_b64decode(given + "====")
        except binascii.Error:
            return False

        return hmac.compare_digest(my[:10], given)


class SyntheticCardIconHandler(BaseAssrValidating):
    async def get(self, frame_info, asset_hex, assr, filetype):
        if not self.validate_assr(f"ci/{frame_info}/{asset_hex}", assr):
            self.set_status(403)
            self.write(ERR_REQUEST_NOAUTH)
            return

        if asset_hex.startswith("-"):
            asset_id = base64.urlsafe_b64decode("".join((asset_hex[1:], "===="))).decode("utf8")
        else:
            asset_id = binascii.unhexlify(asset_hex).decode("utf8")
        fsp = from_frame_info(frame_info)

        try:
            image = await self.settings["extract_contexts"][""].get_cardicon(
                asset_id, filetype, *fsp
            )
        except ExtractFailure as e:
            if e.reason == 1:
                self.set_status(404)
                self.write(str(e))
                return
            else:
                self.set_status(503)
                self.write(str(e))
                return

        self.set_status(200)

        if filetype == "jpg":
            self.set_header("Content-Type", "image/jpeg")
        else:
            self.set_header("Content-Type", "image/png")

        self.write(image)


class SyntheticCardResizeHandler(BaseAssrValidating):
    async def get(self, size, axis, asset_b64, assr, filetype):
        if not self.validate_assr(f"thumb/{size}{axis}/{asset_b64}", assr):
            self.set_status(403)
            self.write(ERR_REQUEST_NOAUTH)
            return

        asset_id = base64.urlsafe_b64decode("".join((asset_b64, "===="))).decode("utf8")

        try:
            image = await self.settings["extract_contexts"][""].get_resized(
                asset_id, filetype, int(size), axis
            )
        except ExtractFailure as e:
            if e.reason == 1:
                self.set_status(404)
                self.write(str(e))
                return
            else:
                self.set_status(503)
                self.write(str(e))
                return

        self.set_status(200)

        if filetype == "jpg":
            self.set_header("Content-Type", "image/jpeg")
        else:
            self.set_header("Content-Type", "image/png")

        self.write(image)


class AdvScriptHandler(BaseAssrValidating):
    def get(self, scpt_name, assr, region=""):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")

        if not self.validate_assr(f"adv/{scpt_name}", assr):
            self.set_status(403)
            self.write({"error": ERR_REQUEST_NOAUTH})
            return

        ec = self.settings["extract_contexts"].get(region)
        if not ec:
            self.set_status(404)
            self.write({"error": ERR_REQUEST_NO_REGION})
            return

        try:
            scpt_bundle = ec.get_script(scpt_name)
        except ExtractFailure:
            self.set_status(404)
            self.write({"error": "Script not found."})
            return

        script = adv_script_parser.load_script(scpt_bundle)

        self.write(
            json.dumps(
                {"result": {"rsrc": script.res_seg, "data": script.data_seg,}}, ensure_ascii=False
            )
        )


class AdvScriptGraphicHandler(RequestHandler):
    async def get(self, scpt_name, idx):
        did_headers = False
        buf = bytearray(65536)

        try:
            file_gen = self.settings["extract_contexts"][""].get_script_texture(
                scpt_name, int(idx), buf
            )
            file_info = next(file_gen)
            etag = hashlib.sha224(file_info["file_id"].encode("utf8")).hexdigest()[:32]
            self.set_header("Etag", f'W/"{etag}"')

            if self.check_etag_header():
                self.set_status(304)
                return

            for buf, size in file_gen:
                if not did_headers:
                    img_type = imghdr.what(None, buf)
                    if img_type:
                        self.set_header("Content-Type", f"image/{img_type}")
                    did_headers = True

                self.write(bytes(buf[:size]))
                await self.flush()
        except ExtractFailure as e:
            self.set_status(404)
            self.write(str(e))
