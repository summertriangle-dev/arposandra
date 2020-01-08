import os
import binascii
import hmac
import hashlib
import base64
import imghdr
import logging

from tornado.web import Application, RequestHandler
from tornado.iostream import StreamClosedError

from libcard2.utils import from_frame_info
from .extract import ExtractContext, ExtractFailure

# from .inspect_backend import InspectState


def _test_for_ffd8(h, f):
    if h[0:2] == b"\xff\xd8":
        return "jpeg"


if _test_for_ffd8 not in imghdr.tests:
    imghdr.tests.append(_test_for_ffd8)


def application(master, debug):
    application = AssetServerApplication(
        master,
        [
            (r"/i/((?:[0-9a-f][0-9a-f])+)/([^/\.]+)(?:\.(?:png|jpg))?", ReifyHandler),
            (
                r"/s/ci/([sgrz][vpuky][mpcanex])/([0-9a-f]+)/([^/]+)\.(jpg|png)",
                SyntheticCardIconHandler,
            ),
            # legacy urls with ?assr= argument
            (r"/i/((?:[0-9a-f][0-9a-f])+)(?:\.(?:png|jpg))?", ReifyHandler),
            (r"/t_reify/(.*)", TestHmacGuardAccess),
            # (r"/api/inspect/hello", InspectServerInfo),
            # (r"/api/inspect/lookup", InspectLookupAsset),
            # (r"/api/inspect/texture", InspectRealizeTexture),
            # (r"/api/inspect/bundle/((?:[0-9a-f][0-9a-f])+)", InspectOpenUnityBundle),
            # (r"/api/inspect/bundle/((?:[0-9a-f][0-9a-f])+)/([0-9a-f]{16})", InspectGetUnityBundleData),
        ],
        debug=debug,
    )
    return application


class AssetServerApplication(Application):
    def __init__(self, masters, *args, **kwargs):
        super().__init__(*args, **kwargs)

        master = os.path.join(masters, "asset_i_ja_0.db")
        cache = os.path.join(os.environ.get("AS_DATA_ROOT"), "cache")
        secret = binascii.unhexlify(os.environ.get("AS_ASSET_JIT_SECRET"))

        if not all((master, cache)):
            raise ValueError("Configuration incomplete")

        self.settings["extract_context"] = ExtractContext(master, cache)
        self.settings["jit_secret"] = secret
        # self.settings["inspect_context"] = InspectState(masters, cache, storage)

    def change_asset_db(self, newdb):
        self.settings["extract_context"].change_asset_db(newdb)


class TestHmacGuardAccess(RequestHandler):
    def get(self, key):
        if not self.settings.get("debug"):
            self.set_status(403)
            self.write("This endpoint is only available in development mode.")
            return

        hx = binascii.hexlify(key.encode("utf8")).decode("ascii")
        my = hmac.new(self.settings["jit_secret"], hx.encode("ascii"), hashlib.sha224).digest()[:10]
        my = base64.urlsafe_b64encode(my).decode("ascii").rstrip("=")
        return self.redirect(f"/reify/{hx}?assr={my}")


######################################################
# HANDLERS
######################################################

ERR_REQUEST_NOAUTH = "Your image request was declined because it was not properly authenticated."


class ReifyHandler(RequestHandler):
    async def get(self, key, assr=None):
        my = hmac.new(self.settings["jit_secret"], key.encode("ascii"), hashlib.sha224).digest()[
            :10
        ]

        if not assr:
            assr = self.get_argument("assr")

        try:
            assr = base64.urlsafe_b64decode(assr + "====")
        except binascii.Error:
            self.set_status(400)
            self.write(ERR_REQUEST_NOAUTH)
            return

        if not hmac.compare_digest(my, assr):
            self.set_status(400)
            self.write(ERR_REQUEST_NOAUTH)
            return

        key = binascii.unhexlify(key).decode("utf8")

        did_headers = False
        buf = bytearray(65536)
        for buf, size in self.settings["extract_context"].get_texture(key, buf):
            if not did_headers:
                img_type = imghdr.what(None, buf)
                if img_type:
                    self.set_header("Content-Type", f"image/{img_type}")
            self.write(bytes(buf[:size]))
            await self.flush()


class SyntheticCardIconHandler(RequestHandler):
    def validate_assr(self, value, given):
        my = hmac.new(self.settings["jit_secret"], value.encode("utf8"), hashlib.sha224).digest()[
            :10
        ]

        try:
            given = base64.urlsafe_b64decode(given + "====")
        except binascii.Error:
            return False

        return hmac.compare_digest(my, given)

    async def get(self, frame_info, asset_hex, assr, filetype):
        if not self.validate_assr(f"ci/{frame_info}/{asset_hex}", assr):
            self.set_status(400)
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
