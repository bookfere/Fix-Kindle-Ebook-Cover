"""
Detect image format from the first bytes of a byte stream.

No third-party dependencies. Returns the same format names as imghdr:
'jpeg', 'png', 'gif', 'tiff', 'rgb', 'pbm', 'pgm', 'ppm',
'rast', 'xbm', 'bmp', 'webp', 'exr'.
"""


def detect_image_format(data):
    """
    Detect image format from a bytes-like object.

    :param data: bytes, bytearray, or memoryview containing image data.
    :return: format name as str, or None if unknown.
    """
    if data is None:
        return None

    try:
        head = bytes(data[:32])
    except TypeError:
        raise TypeError("data must be a bytes-like object")

    if len(head) < 2:
        return None

    if len(head) >= 3 and head[0:2] == b"\xff\xd8" and head[2] == 0xFF:
        return "jpeg"

    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"

    if head.startswith((b"GIF87a", b"GIF89a")):
        return "gif"

    if head.startswith((b"II*\x00", b"MM\x00*")):
        return "tiff"

    if head.startswith(b"\x01\xda"):
        return "rgb"

    if len(head) >= 3 and head[0] == 0x50 and head[2] in b" \t\n\r":
        if head[1] in b"14":
            return "pbm"
        if head[1] in b"25":
            return "pgm"
        if head[1] in b"36":
            return "ppm"

    if head.startswith(b"\x59\xa6\x6a\x95"):
        return "rast"

    if head.startswith(b"#define "):
        return "xbm"

    if head.startswith(b"BM"):
        return "bmp"

    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "webp"

    if head.startswith(b"\x76\x2f\x31\x01"):
        return "exr"

    return None
