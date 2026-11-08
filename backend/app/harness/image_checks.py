"""Structural PNG validation without an image-library dependency."""

import struct
import zlib

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def is_decodable_png(data: bytes) -> bool:
    """Return True when ``data`` is a complete PNG with decodable pixel data."""
    if not data.startswith(PNG_SIGNATURE):
        return False

    offset = len(PNG_SIGNATURE)
    dimensions: tuple[int, int] | None = None
    compressed_pixels = bytearray()
    saw_end = False

    while offset + 8 <= len(data):
        length = int.from_bytes(data[offset : offset + 4], "big")
        chunk_type = data[offset + 4 : offset + 8]
        payload_start = offset + 8
        payload_end = payload_start + length
        if payload_end + 4 > len(data):
            return False

        payload = data[payload_start:payload_end]
        expected_crc = int.from_bytes(data[payload_end : payload_end + 4], "big")
        if zlib.crc32(chunk_type + payload) & 0xFFFFFFFF != expected_crc:
            return False

        if chunk_type == b"IHDR":
            if length != 13:
                return False
            width, height = struct.unpack(">II", payload[:8])
            if width == 0 or height == 0:
                return False
            dimensions = (width, height)
        elif chunk_type == b"IDAT":
            compressed_pixels.extend(payload)
        elif chunk_type == b"IEND":
            saw_end = True
            break

        offset = payload_end + 4

    if dimensions is None or not compressed_pixels or not saw_end:
        return False

    try:
        zlib.decompress(bytes(compressed_pixels))
    except zlib.error:
        return False
    return True
