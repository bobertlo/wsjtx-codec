"""
test_qdatastream_writer.py — pytest harness for QDataStreamWriter.
"""

import math
import struct
from datetime import datetime, timedelta, timezone

import pytest

from wsjtx_codec.qdatastream import QDataStreamWriter
from tests.qdatastream_helpers import reader


def _roundtrip(write_fn, read_fn, value):
    """Write value, read it back, return decoded result."""
    w = QDataStreamWriter()
    write_fn(w, value)
    return read_fn(reader(w.getvalue()))


# ---------------------------------------------------------------------------
# u8
# ---------------------------------------------------------------------------

U8_CASES = [0, 1, 127, 128, 255]


@pytest.mark.parametrize("v", U8_CASES)
def test_write_u8_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_u8, lambda r: r.read_u8(), v) == v


# ---------------------------------------------------------------------------
# bool
# ---------------------------------------------------------------------------


def test_write_bool_false_bytes():
    w = QDataStreamWriter()
    w.write_bool(False)
    assert w.getvalue() == b"\x00"


def test_write_bool_true_bytes():
    w = QDataStreamWriter()
    w.write_bool(True)
    assert w.getvalue() == b"\x01"


@pytest.mark.parametrize("v", [False, True])
def test_write_bool_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_bool, lambda r: r.read_bool(), v) == v


# ---------------------------------------------------------------------------
# u32
# ---------------------------------------------------------------------------

U32_CASES = [0, 1, 0xADBCCD, 0xFFFFFFFE, 0xFFFFFFFF]


@pytest.mark.parametrize("v", U32_CASES)
def test_write_u32_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_u32, lambda r: r.read_u32(), v) == v


# ---------------------------------------------------------------------------
# i32
# ---------------------------------------------------------------------------

I32_CASES = [0, 1, -1, 2147483647, -2147483648, -15]


@pytest.mark.parametrize("v", I32_CASES)
def test_write_i32_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_i32, lambda r: r.read_i32(), v) == v


# ---------------------------------------------------------------------------
# i64
# ---------------------------------------------------------------------------

I64_CASES = [0, 1, -1, 9223372036854775807, -9223372036854775808, 1_700_000_000_000]


@pytest.mark.parametrize("v", I64_CASES)
def test_write_i64_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_i64, lambda r: r.read_i64(), v) == v


# ---------------------------------------------------------------------------
# u64
# ---------------------------------------------------------------------------

U64_CASES = [0, 1, 7_074_000, 0xFFFFFFFFFFFFFFFF]


@pytest.mark.parametrize("v", U64_CASES)
def test_write_u64_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_u64, lambda r: r.read_u64(), v) == v


# ---------------------------------------------------------------------------
# f64
# ---------------------------------------------------------------------------

F64_CASES = [0.0, 1.0, -1.0, -12.5, 0.1, math.inf, -math.inf]


@pytest.mark.parametrize("v", F64_CASES)
def test_write_f64_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_f64, lambda r: r.read_f64(), v) == v


def test_write_f64_nan_roundtrip():
    w = QDataStreamWriter()
    w.write_f64(math.nan)
    assert math.isnan(reader(w.getvalue()).read_f64())


# ---------------------------------------------------------------------------
# utf8
# ---------------------------------------------------------------------------


def test_write_utf8_null_bytes():
    w = QDataStreamWriter()
    w.write_utf8(None)
    assert w.getvalue() == b"\xff\xff\xff\xff"


def test_write_utf8_empty_bytes():
    w = QDataStreamWriter()
    w.write_utf8("")
    assert w.getvalue() == b"\x00\x00\x00\x00"


UTF8_CASES = [None, "", "K0SWE", "CQ DX W1AW FN31", "☃", "de DF0MU/p"]


@pytest.mark.parametrize("v", UTF8_CASES)
def test_write_utf8_roundtrip(v):
    assert _roundtrip(QDataStreamWriter.write_utf8, lambda r: r.read_utf8(), v) == v


# ---------------------------------------------------------------------------
# qdatetime
# ---------------------------------------------------------------------------

QDATETIME_CASES = [
    datetime(2000, 1, 1, tzinfo=timezone.utc),
    datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
    datetime(2020, 10, 30, 11, 29, 57, 320000, tzinfo=timezone.utc),
    datetime(2000, 1, 1),  # naive / local
    datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone(timedelta(seconds=3600))),
    datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone(timedelta(seconds=-18000))),
]


@pytest.mark.parametrize("v", QDATETIME_CASES)
def test_write_qdatetime_roundtrip(v):
    assert (
        _roundtrip(QDataStreamWriter.write_qdatetime, lambda r: r.read_qdatetime(), v)
        == v
    )


def test_write_qdatetime_utc_timespec_byte():
    """UTC datetimes must encode timespec=1."""
    w = QDataStreamWriter()
    w.write_qdatetime(datetime(2000, 1, 1, tzinfo=timezone.utc))
    data = w.getvalue()
    # timespec byte is at offset 12 (8 bytes JDN + 4 bytes ms)
    assert data[12] == 1


def test_write_qdatetime_naive_timespec_byte():
    """Naive datetimes must encode timespec=0."""
    w = QDataStreamWriter()
    w.write_qdatetime(datetime(2000, 1, 1))
    assert w.getvalue()[12] == 0


def test_write_qdatetime_offset_timespec_byte():
    """Fixed-offset datetimes must encode timespec=2 followed by offset i32."""
    w = QDataStreamWriter()
    w.write_qdatetime(datetime(2000, 1, 1, tzinfo=timezone(timedelta(hours=5))))
    data = w.getvalue()
    assert data[12] == 2
    assert len(data) == 17  # 8 + 4 + 1 + 4 = JDN + ms + timespec + offset


# ---------------------------------------------------------------------------
# sequential writes and getvalue type
# ---------------------------------------------------------------------------


def test_getvalue_returns_bytes():
    w = QDataStreamWriter()
    w.write_u8(0)
    assert type(w.getvalue()) is bytes


def test_sequential_writes_heartbeat():
    """Build the fixed portion of a HEARTBEAT header and read it back."""
    magic = 0xADBCCBDA
    w = QDataStreamWriter()
    w.write_u32(magic)
    w.write_u32(2)  # schema
    w.write_u32(0)  # type = heartbeat
    w.write_utf8("WSJT-X")
    w.write_u32(3)  # max_schema

    r = reader(w.getvalue())
    assert r.read_u32() == magic
    assert r.read_u32() == 2
    assert r.read_u32() == 0
    assert r.read_utf8() == "WSJT-X"
    assert r.read_u32() == 3
    r.assert_empty()


# ===========================================================================
# Byte-exact cases — inverse of reader test suite
#
# Each parametrize tuple is (value_to_write, expected_raw_bytes).
# Expected bytes use struct.pack or byte literals directly — not the test
# helpers — so these tests remain independent of the writer under test.
# ===========================================================================

_J2000 = 2451545  # JDN of 2000-01-01 (mirrors test_qdatastream.py)
_JDN_20201030 = 2459153  # JDN of 2020-10-30


def _raw_dt(jdn: int, ms: int, timespec: int, offset: int | None = None) -> bytes:
    data = struct.pack(">qI", jdn, ms) + bytes([timespec])
    if offset is not None:
        data += struct.pack(">i", offset)
    return data


def _write_bytes(method, value) -> bytes:
    w = QDataStreamWriter()
    method(w, value)
    return w.getvalue()


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00"),
        (128, b"\x80"),
        (255, b"\xff"),
    ],
)
def test_write_u8_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_u8, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (False, b"\x00"),
        (True, b"\x01"),
    ],
)
def test_write_bool_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_bool, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00\x00\x00\x00"),
        (1, b"\x00\x00\x00\x01"),
        (0xADBCCD, b"\x00\xad\xbc\xcd"),
        (29010001, struct.pack(">I", 29010001)),
        (0x304, b"\x00\x00\x03\x04"),
        (0xFFFFFFFE, b"\xff\xff\xff\xfe"),
        (0xFFFFFFFF, b"\xff\xff\xff\xff"),
    ],
)
def test_write_u32_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_u32, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00\x00\x00\x00"),
        (1, b"\x00\x00\x00\x01"),
        (-1, b"\xff\xff\xff\xff"),
        (2147483647, b"\x7f\xff\xff\xff"),  # INT32_MAX
        (-2147483648, b"\x80\x00\x00\x00"),  # INT32_MIN
        (-15, b"\xff\xff\xff\xf1"),  # typical SNR
    ],
)
def test_write_i32_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_i32, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        (1, b"\x00\x00\x00\x00\x00\x00\x00\x01"),
        (-1, b"\xff\xff\xff\xff\xff\xff\xff\xff"),
        (9223372036854775807, b"\x7f\xff\xff\xff\xff\xff\xff\xff"),  # INT64_MAX
        (-9223372036854775808, b"\x80\x00\x00\x00\x00\x00\x00\x00"),  # INT64_MIN
        (1_700_000_000_000, struct.pack(">q", 1_700_000_000_000)),  # ms timestamp
    ],
)
def test_write_i64_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_i64, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (0.0, b"\x00\x00\x00\x00\x00\x00\x00\x00"),
        (1.0, b"\x3f\xf0\x00\x00\x00\x00\x00\x00"),
        (-1.0, b"\xbf\xf0\x00\x00\x00\x00\x00\x00"),
        (-12.5, b"\xc0\x29\x00\x00\x00\x00\x00\x00"),
        (0.1, struct.pack(">d", 0.1)),
        (math.inf, b"\x7f\xf0\x00\x00\x00\x00\x00\x00"),
        (-math.inf, b"\xff\xf0\x00\x00\x00\x00\x00\x00"),
    ],
)
def test_write_f64_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_f64, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, b"\xff\xff\xff\xff"),
        ("", b"\x00\x00\x00\x00"),
        ("K0SWE", b"\x00\x00\x00\x05" + b"K0SWE"),
        ("CQ DX W1AW FN31", b"\x00\x00\x00\x0f" + b"CQ DX W1AW FN31"),
        ("de DF0MU/p", b"\x00\x00\x00\x0a" + b"de DF0MU/p"),
        ("☃", b"\x00\x00\x00\x03\xe2\x98\x83"),  # snowman, 3-byte UTF-8
    ],
)
def test_write_utf8_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_utf8, value) == expected


@pytest.mark.parametrize(
    "value, expected",
    [
        (datetime(2000, 1, 1, tzinfo=timezone.utc), _raw_dt(_J2000, 0, 1)),
        (
            datetime(2000, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            _raw_dt(_J2000, 43200000, 1),
        ),
        (
            datetime(2020, 10, 30, 11, 29, 57, 320000, tzinfo=timezone.utc),
            _raw_dt(_JDN_20201030, 41397320, 1),
        ),
        (
            datetime(2020, 10, 30, 11, 28, 57, 320000, tzinfo=timezone.utc),
            _raw_dt(_JDN_20201030, 41337320, 1),
        ),
        (datetime(2000, 1, 1), _raw_dt(_J2000, 0, 0)),
        (
            datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone(timedelta(seconds=3600))),
            _raw_dt(_J2000, 3600000, 2, 3600),
        ),
        (
            datetime(2000, 1, 1, 1, 0, 0, tzinfo=timezone(timedelta(seconds=-18000))),
            _raw_dt(_J2000, 3600000, 2, -18000),
        ),
    ],
)
def test_write_qdatetime_bytes(value, expected):
    assert _write_bytes(QDataStreamWriter.write_qdatetime, value) == expected
