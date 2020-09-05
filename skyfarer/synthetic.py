import os
import tempfile
import logging
import io
import ctypes
import struct
import binascii
from contextlib import contextmanager

from PIL import Image
from PIL.PngImagePlugin import PngInfo

import hwdecrypt

### BEGIN EXTERNAL PROCESS CODE ###

# only initialized in external processes (hopefully)
G_CARD_ICON_ATLAS = None

frame_coordinate = {1: (128, 128, 256, 256), 2: (0, 128, 128, 256), 3: (0, 0, 128, 128)}


def grid_calc(base, size, where, rgn_size):
    x = where[0] * size[0]
    y = where[1] * size[1]
    return (base[0] + x, base[1] + y, base[0] + x + rgn_size[0], base[1] + y + rgn_size[1])


attribute_coordinate = {
    1: grid_calc((128, 0), (30, 30), (0, 0), (28, 28)),
    2: grid_calc((128, 0), (30, 30), (1, 0), (28, 28)),
    3: grid_calc((128, 0), (30, 30), (2, 0), (28, 28)),
    4: grid_calc((128, 0), (30, 30), (0, 1), (28, 28)),
    5: grid_calc((128, 0), (30, 30), (1, 1), (28, 28)),
    6: grid_calc((128, 0), (30, 30), (2, 1), (28, 28)),
}
role_coordinate = {
    1: grid_calc((128, 0), (30, 30), (0, 2), (28, 28)),
    2: grid_calc((128, 0), (30, 30), (1, 2), (28, 28)),
    3: grid_calc((128, 0), (30, 30), (0, 3), (28, 28)),
    4: grid_calc((128, 0), (30, 30), (1, 3), (28, 28)),
}


def make_exif(s: bytes) -> bytes:
    head = binascii.unhexlify("4578696600004D4D002A00000008000101310002")
    size = struct.pack(">IIxxxx", len(s), len(head) + 6)
    return b"".join((head, size, s))


def make_icon_exif(f, a, r):
    meta = f"Skyfarer v:2,f:{f},a:{a},r:{r}\x00".encode("ascii")
    return make_exif(meta)


def load_image(packid, head, size, k1, k2, k3):
    idata = io.BytesIO()
    idata.seek(size - 1)
    idata.write(b".")
    idata.seek(0)

    with open(packid, "rb") as f:
        f.seek(head)
        if f.readinto(idata.getbuffer()) != size:
            raise IOError("Not enough data")

    keyset = hwdecrypt.Keyset(k1, k2, k3)
    hwdecrypt.decrypt(keyset, idata.getbuffer())
    idata.seek(0)
    return Image.open(idata)


def stack_card(image_load_args, fmt, frame_num, role_num, attr_num):
    global G_CARD_ICON_ATLAS

    if not frame_num < 4:
        return (1, None)
    if not role_num < 5:
        return (1, None)
    if not attr_num < 7:
        return (1, None)

    if not G_CARD_ICON_ATLAS:
        try:
            G_CARD_ICON_ATLAS = Image.open(
                os.path.join(os.path.dirname(__file__), "assets", "cardicons.png")
            )
        except IOError:
            return (1, None)

    try:
        face = load_image(*image_load_args)
    except IOError:
        return (1, None)

    icon = Image.new("RGBA", (128, 128))
    icon.paste(face, ((icon.size[0] - face.size[0]) // 2, (icon.size[1] - face.size[1]) // 2))
    if frame_num:
        icon.alpha_composite(G_CARD_ICON_ATLAS, source=frame_coordinate[frame_num])
    if attr_num:
        icon.alpha_composite(G_CARD_ICON_ATLAS, (97, 3), attribute_coordinate[attr_num])
    if role_num:
        icon.alpha_composite(G_CARD_ICON_ATLAS, (2, 98), role_coordinate[role_num])

    bio = io.BytesIO()
    try:
        if fmt == "jpg":
            icon.convert("RGB").save(
                bio, "jpeg", quality=90, exif=make_icon_exif(frame_num, attr_num, role_num)
            )
        else:
            meta = PngInfo()
            meta.add_text("Skyfarer", f"v:2,f:{frame_num},a:{attr_num},r:{role_num}")
            icon.save(bio, "png", optimize=True, pnginfo=meta)
    except IOError:
        return (3, None)

    return (0, bio.getvalue())


def resize_card(image_load_args, fmt, height, axis):
    try:
        image = load_image(*image_load_args)
    except IOError:
        return (1, None)

    scalefactor = height / (image.height if axis == "h" else image.width)

    if image.format == "PNG" and (image.mode != "RGB" or image.mode != "RGBA"):
        image = image.convert("RGBA")

    image = image.resize(
        (round(image.width * scalefactor), round(image.height * scalefactor)), reducing_gap=3.0
    )
    bio = io.BytesIO()
    try:
        if fmt == "jpg":
            image.save(bio, "jpeg", quality=90, exif=make_exif(b"SkyfarerGalleryResizeTag"))
        else:
            meta = PngInfo()
            meta.add_text("Skyfarer", f"GalleryResizeTag")
            image.save(bio, "png", optimize=True, pnginfo=meta)
    except IOError as e:
        return (3, None)

    return (0, bio.getvalue())


### END EXTERNAL PROCESS CODE ###
