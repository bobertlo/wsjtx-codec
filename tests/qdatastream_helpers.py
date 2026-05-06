"""
qdatastream_helpers.py - helper functions to mock input
"""

import struct
from datetime import datetime

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


def qdatetime_utc(dt: datetime) -> bytes:
    _JDN_ORDINAL_OFFSET = 1721425
    jdn = dt.toordinal() + _JDN_ORDINAL_OFFSET
    ms = (dt.hour * 3600 + dt.minute * 60 + dt.second) * 1000 + (dt.microsecond // 1000)
    return i64(jdn) + u32(ms) + b"\x01"


def qt_string(s: str | None) -> bytes:
    if s is None:
        return b"\xff\xff\xff\xff"
    encoded = s.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded
