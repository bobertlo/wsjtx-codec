"""
qdatastream_helpers.py - helper functions to mock input
"""

import struct

from wsjtx_codec.qdatastream import QDataStreamReader


def reader(data: bytes) -> QDataStreamReader:
    return QDataStreamReader(data, version=18)


def u32(n: int) -> bytes:
    return struct.pack(">I", n)


def i32(n: int) -> bytes:
    return struct.pack(">i", n)


def i64(n: int) -> bytes:
    return struct.pack(">q", n)


def u64(n: int) -> bytes:
    return struct.pack(">Q", n)


def f64(n: float) -> bytes:
    return struct.pack(">d", n)


def bool_byte(b: bool) -> bytes:
    return b"\x01" if b else b"\x00"


def qt_string(s: str | None) -> bytes:
    if s is None:
        return b"\xff\xff\xff\xff"
    encoded = s.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded
