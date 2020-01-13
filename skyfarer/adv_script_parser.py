# @(#)All Stars ADV script decompressor
# @(#)Copyright 2020, t
# https://github.com/summertriangle-dev/arposandra/blob/master/LICENSE.md

import sys
import struct
from collections import namedtuple

__all__ = ["load_script", "adv_script_t"]

kADVHeaderLength         = 0x1b                  # 0?
kADVMagic                = 0x80                  # 0x28
kADVHasCompressionMask   = 0x80                  # 0x29
kADVHasResSegMask        = 0x40                  # 0x2A

kADVCTagLength           = 3
kADVCTagSignal           = 0x80

adv_header_t = namedtuple("adv_header_t", (
    "magic",            # [1] kADVMagic.
    "data_flags",       # [1] Bitmask. Has kADVHasResSegMask if there is a
                        #   resource segment, and kADVHasCompressionMask if compressed.
    "data_start",       # [4] Start of compressed data segment from position zero.
                        #   If the file has compressed segments, this can be less than
                        #   res_start + res_length.
    "res_start",        # [4] Start of compressed resource segment from position zero.
    "data_length",      # [4] Length of decompressed data segment.
    "res_length",       # [4] Length of decompressed resource segment.
    "check",            # [1] Does not appear to be used.
    "nonce",            # [4] Does not appear to be used.
    "key_nonce",        # [4] Does not appear to be used.
))

adv_header_t._description = struct.Struct("<BBIIIIBII")
adv_header_t._frombytes = lambda bstr: adv_header_t._make(adv_header_t._description.unpack(bstr))

adv_script_t = namedtuple("adv_script_t", ("res_seg", "data_seg"))

def utf8_calc(c: int):
    if c >= 0b11110000:
        return 4
    elif c >= 0b11100000:
        return 3
    elif c >= 0b11000000:
        return 2
    else:
        return 1

def decompress_internal(scptbuf: bytes, where: int, full_size: int) -> str:
    """
    Script compression uses a simple backreferencing algorithm.
    A 0x80 byte that is not part of a UTF-8 code unit signals the start of
    a reference. You should then copy `*(tag + 2) + 1` bytes starting from
    `c_pos + ~(*(tag + 1))`.
    """
    nwrit = 0
    out = bytearray(full_size)

    while nwrit < full_size:
        if scptbuf[where] == kADVCTagSignal:
            backstep = ~scptbuf[where + 1]
            cbase = nwrit + backstep
            ncopy = scptbuf[where + 2] + 1

            if ncopy > -backstep:
                unit_size = -backstep
                for i in range(ncopy // -backstep):
                    out[nwrit:nwrit + unit_size] = out[cbase:cbase + unit_size]
                    nwrit += unit_size
            else:
                out[nwrit:nwrit + ncopy] = out[cbase:cbase + ncopy]
                nwrit += ncopy

            where += kADVCTagLength
        else:
            ncopy = utf8_calc(scptbuf[where])
            out[nwrit:nwrit + ncopy] = scptbuf[where:where + ncopy]
            where += ncopy
            nwrit += ncopy

    return out.decode("utf8")

def load_script(scptbuf: bytes) -> adv_script_t:
    header = adv_header_t._frombytes(scptbuf[:kADVHeaderLength])
    if header.magic != kADVMagic:
        raise ValueError("Incorrect start byte, it should be kADVMagic.")

    res = None

    if header.data_flags & kADVHasCompressionMask:
        if header.data_flags & kADVHasResSegMask:
            res = decompress_internal(scptbuf, header.res_start, header.res_length)
        dat = decompress_internal(scptbuf, header.data_start, header.data_length)
    else:
        if header.data_flags & kADVHasResSegMask:
            res = scptbuf[header.res_start:header.res_start + header.res_length].decode("utf8")
        dat = scptbuf[header.res_start:header.data_start + header.data_length].decode("utf8")

    return adv_script_t(res, dat)

def main():
    with open(sys.argv[1], "rb") as scpt:
        scptbuf = scpt.read()

    header = adv_header_t._frombytes(scptbuf[:kADVHeaderLength])
    print("# \x64(#)ADV script summary from:", sys.argv[1])
    print("# \x64(#)Resource segment?", "YES" if (header.data_flags & kADVHasResSegMask) else "NO",
        "Compressed segments?", "YES" if (header.data_flags & kADVHasCompressionMask) else "NO")
    print("# \x64(#)Textual script header:", header)

    scpt = load_script(scptbuf)

    if header.data_flags & kADVHasResSegMask:
        print("\n\n\n# ------- BEGIN RESOURCE SEGMENT ---------------------")
        print(scpt.res_seg)
        print("# ------- END RESOURCE SEGMENT -----------------------")

    print("\n\n\n# ------- BEGIN DATA SEGMENT -------------------------")
    print(scpt.data_seg)
    print("# ------- END DATA SEGMENT ---------------------------")

if __name__ == '__main__':
    main()