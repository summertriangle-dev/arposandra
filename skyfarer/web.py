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


def application(master, language, debug):
    application = AssetServerApplication(
        master,
        language,
        [
            (r"/i/((?:[0-9a-f][0-9a-f])+)/([^/\.]+)(?:\.(?:png|jpg))?", ReifyHandler),
            (
                r"/s/ci/([sgrz][vpuky][mpcanex])/([0-9a-f]+)/([^/]+)\.(jpg|png)",
                SyntheticCardIconHandler,
            ),
            (r"/adv/(.+)/([^/\.]+)\.json", AdvScriptHandler),
            (r"/advg/(.+)/([0-9]+)\.(?:png|jpg)", AdvScriptGraphicHandler),
            (r"/if/(.+)/([^/\.]+)(?:\.(?:png|jpg))?", BareReifyHandler),
            # (r"/api/inspect/hello", InspectServerInfo),
            # (r"/api/inspect/lookup", InspectLookupAsset),
            # (r"/api/inspect/texture", InspectRealizeTexture),
            # (r"/api/inspect/bundle/((?:[0-9a-f][0-9a-f])+)", InspectOpenUnityBundle),
            # (r"/api/inspect/bundle/((?:[0-9a-f][0-9a-f])+)/([0-9a-f]{16})", InspectGetUnityBundleData),
        ],
        debug=debug,
        disable_security=debug,
    )
    return application


class AssetServerApplication(Application):
    def __init__(self, masters, language, *args, **kwargs):
        super().__init__(*args, **kwargs)

        master = os.path.join(masters, f"asset_i_{language}.db")
        cache = os.path.join(masters, "..", "..", "cache")
        secret = binascii.unhexlify(os.environ.get("AS_ASSET_JIT_SECRET"))

        if not all((master, cache)):
            raise ValueError("Configuration incomplete")

        self.settings["extract_context"] = ExtractContext(master, cache)
        self.settings["jit_secret"] = secret
        # self.settings["inspect_context"] = InspectState(masters, cache, storage)

    def change_asset_db(self, newdb):
        self.settings["extract_context"].change_asset_db(newdb)


######################################################
# HANDLERS
######################################################

ERR_REQUEST_NOAUTH = "Your request was declined because it was not properly authenticated."


class BareReifyHandler(RequestHandler):
    async def get(self, key, assr):
        my = hmac.new(self.settings["jit_secret"], key.encode("utf8"), hashlib.sha224).digest()

        try:
            assr = base64.urlsafe_b64decode(assr + "====")
        except binascii.Error:
            self.set_status(400)
            self.write(ERR_REQUEST_NOAUTH)
            return

        if not hmac.compare_digest(my[:10], assr):
            if not self.settings["disable_security"]:
                self.set_status(403)
                self.write(ERR_REQUEST_NOAUTH)
                return

        did_headers = False
        buf = bytearray(65536)

        try:
            file_gen = self.settings["extract_context"].get_texture(key, buf)
        except ExtractFailure as e:
            if e.reason == 1:
                self.set_status(404)
                self.write(str(e))
                return
            else:
                self.set_status(503)
                self.write(str(e))
                return

        for buf, size in file_gen:
            if not did_headers:
                img_type = imghdr.what(None, buf)
                if img_type:
                    self.set_header("Content-Type", f"image/{img_type}")
                did_headers = True
            self.write(bytes(buf[:size]))
            await self.flush()


class ReifyHandler(BareReifyHandler):
    async def get(self, key, assr):
        try:
            key = binascii.unhexlify(key).decode("utf8")
        except UnicodeDecodeError:
            self.set_status(400)
            return

        await super().get(key, assr)


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

        asset_id = binascii.unhexlify(asset_hex).decode("utf8")
        fsp = from_frame_info(frame_info)

        try:
            image = await self.settings["extract_context"].get_cardicon(asset_id, filetype, *fsp)
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
    def get(self, scpt_name, assr):
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Content-Type", "application/json")

        if not self.validate_assr(f"adv/{scpt_name}", assr):
            self.set_status(403)
            self.write({"error": ERR_REQUEST_NOAUTH})
            return

        try:
            scpt_bundle = self.settings["extract_context"].get_script(scpt_name)
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
            file_gen = self.settings["extract_context"].get_script_texture(scpt_name, int(idx), buf)
        except ExtractFailure as e:
            self.set_status(404)
            self.write(str(e))

        for buf, size in file_gen:
            if not did_headers:
                img_type = imghdr.what(None, buf)
                if img_type:
                    self.set_header("Content-Type", f"image/{img_type}")
                did_headers = True

            self.write(bytes(buf[:size]))
            await self.flush()
