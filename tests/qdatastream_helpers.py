"""
qdatastream_helpers.py - helper functions to build test input bytes
"""

from datetime import datetime

from wsjtx_codec.qdatastream import QDataStreamReader, QDataStreamWriter


def reader(data: bytes) -> QDataStreamReader:
    return QDataStreamReader(data, version=18)


def _w() -> QDataStreamWriter:
    return QDataStreamWriter()


def u32(n: int) -> bytes:
    w = _w()
    w.write_u32(n)
    return w.getvalue()


def i32(n: int) -> bytes:
    w = _w()
    w.write_i32(n)
    return w.getvalue()


def i64(n: int) -> bytes:
    w = _w()
    w.write_i64(n)
    return w.getvalue()


def u64(n: int) -> bytes:
    w = _w()
    w.write_u64(n)
    return w.getvalue()


def f64(n: float) -> bytes:
    w = _w()
    w.write_f64(n)
    return w.getvalue()


def bool_byte(b: bool) -> bytes:
    w = _w()
    w.write_bool(b)
    return w.getvalue()


def qdatetime_utc(dt: datetime) -> bytes:
    w = _w()
    w.write_qdatetime(dt)
    return w.getvalue()


def qt_string(s: str | None) -> bytes:
    w = _w()
    w.write_utf8(s)
    return w.getvalue()
