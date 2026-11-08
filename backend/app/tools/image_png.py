"""Minimal deterministic PNG encoder used by the fake image provider."""

import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def encode_solid_png(width: int, height: int, rgb: tuple[int, int, int]) -> bytes:
    """Return a valid RGB PNG with every pixel set to ``rgb``.

    The bytes depend only on the arguments, so identical inputs always
    produce an identical checksum without needing a third-party image library.
    """
    if width < 1 or height < 1:
        raise ValueError("image dimensions must be positive")
    if len(rgb) != 3 or any(component < 0 or component > 255 for component in rgb):
        raise ValueError("rgb must contain three values between 0 and 255")

    raw_row = b"\x00" + bytes(rgb) * width
    raw_pixels = raw_row * height
    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)

    return b"".join(
        (
            PNG_SIGNATURE,
            _chunk(b"IHDR", header),
            _chunk(b"IDAT", zlib.compress(raw_pixels, 9)),
            _chunk(b"IEND", b""),
        )
    )


def _chunk(kind: bytes, payload: bytes) -> bytes:
    crc = zlib.crc32(kind + payload) & 0xFFFFFFFF
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", crc)
