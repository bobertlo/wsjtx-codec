"""
test_qdatastream_reader.py — pytest harness for QDataStreamReader.

"""

import math
import struct

import pytest

from wsjtx_codec.qdatastream import QDataStreamReader


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def reader(data: bytes) -> QDataStreamReader:
    return QDataStreamReader(data, version=18)


def u32(n: int) -> bytes:
    return struct.pack(">I", n)


def i32(n: int) -> bytes:
    return struct.pack(">i", n)


def i64(n: int) -> bytes:
    return struct.pack(">q", n)


def f64(n: float) -> bytes:
    return struct.pack(">d", n)


def qt_string(s: str | None) -> bytes:
    if s is None:
        return b"\xff\xff\xff\xff"
    encoded = s.encode("utf-8")
    return struct.pack(">I", len(encoded)) + encoded


# ---------------------------------------------------------------------------
# read_u8
# ---------------------------------------------------------------------------

U8_CASES = [
    {"input": bytes([0x00]), "expected": 0},
    {"input": bytes([0x80]), "expected": 128},
    {"input": bytes([0xFF]), "expected": 255},
]


@pytest.mark.parametrize("case", U8_CASES)
def test_read_u8(case):
    assert reader(case["input"]).read_u8() == case["expected"]


def test_read_u8_truncated():
    with pytest.raises(EOFError):
        reader(b"").read_u8()


# ---------------------------------------------------------------------------
# read_bool
# ---------------------------------------------------------------------------

BOOL_CASES = [
    {"input": bytes([0x00]), "expected": False},
    {"input": bytes([0x01]), "expected": True},
    {"input": bytes([0xFF]), "expected": True},  # any non-zero → True
]


@pytest.mark.parametrize("case", BOOL_CASES)
def test_read_bool(case):
    assert reader(case["input"]).read_bool() == case["expected"]


def test_read_bool_truncated():
    with pytest.raises(EOFError):
        reader(b"").read_bool()


# ---------------------------------------------------------------------------
# read_u32
# ---------------------------------------------------------------------------

U32_CASES = [
    {"input": u32(0), "expected": 0},
    {"input": u32(1), "expected": 1},
    {"input": u32(0xADBCCD), "expected": 0xADBCCD},
    {"input": u32(29010001), "expected": 29010001},
    {"input": u32(0xFFFFFFFE), "expected": 0xFFFFFFFE},
    {"input": u32(0xFFFFFFFF), "expected": 0xFFFFFFFF},  # raw sentinel value
]


@pytest.mark.parametrize("case", U32_CASES)
def test_read_u32(case):
    assert reader(case["input"]).read_u32() == case["expected"]


def test_read_u32_truncated():
    with pytest.raises(EOFError):
        reader(b"\x00\x00").read_u32()  # only 2 bytes, need 4


# ---------------------------------------------------------------------------
# read_i32
# ---------------------------------------------------------------------------

I32_CASES = [
    {"input": i32(0), "expected": 0},
    {"input": i32(1), "expected": 1},
    {"input": i32(-1), "expected": -1},
    {"input": i32(2147483647), "expected": 2147483647},  # INT32_MAX
    {"input": i32(-2147483648), "expected": -2147483648},  # INT32_MIN
    {"input": i32(-15), "expected": -15},  # typical SNR
]


@pytest.mark.parametrize("case", I32_CASES)
def test_read_i32(case):
    assert reader(case["input"]).read_i32() == case["expected"]


def test_read_i32_truncated():
    with pytest.raises(EOFError):
        reader(b"\x00").read_i32()


# ---------------------------------------------------------------------------
# read_i64
# ---------------------------------------------------------------------------

I64_CASES = [
    {"input": i64(0), "expected": 0},
    {"input": i64(1), "expected": 1},
    {"input": i64(-1), "expected": -1},
    {"input": i64(9223372036854775807), "expected": 9223372036854775807},  # INT64_MAX
    {"input": i64(-9223372036854775808), "expected": -9223372036854775808},  # INT64_MIN
    {"input": i64(1_700_000_000_000), "expected": 1_700_000_000_000},  # ms timestamp
]


@pytest.mark.parametrize("case", I64_CASES)
def test_read_i64(case):
    assert reader(case["input"]).read_i64() == case["expected"]


def test_read_i64_truncated():
    with pytest.raises(EOFError):
        reader(b"\x00\x00\x00\x00").read_i64()  # 4 bytes, need 8


# ---------------------------------------------------------------------------
# read_utf8
# ---------------------------------------------------------------------------

UTF8_CASES = [
    # Qt null QString sentinel
    {"input": qt_string(None), "expected": None},
    # Empty string
    {"input": qt_string(""), "expected": ""},
    # Plain ASCII
    {"input": qt_string("K0SWE"), "expected": "K0SWE"},
    # Typical WSJT-X decode line
    {"input": qt_string("CQ DX W1AW FN31"), "expected": "CQ DX W1AW FN31"},
    # Multi-byte UTF-8 (non-ASCII callsign region)
    {"input": qt_string("de DF0MU/p"), "expected": "de DF0MU/p"},
    # Unicode snowman — ensures raw byte-length prefix, not char-length
    {"input": qt_string("☃"), "expected": "☃"},
]


@pytest.mark.parametrize("case", UTF8_CASES)
def test_read_utf8(case):
    assert reader(case["input"]).read_utf8() == case["expected"]


def test_read_utf8_truncated_header():
    """Length prefix itself is truncated."""
    with pytest.raises(EOFError):
        reader(b"\x00\x00").read_utf8()


def test_read_utf8_truncated_body():
    """Length prefix claims 10 bytes but only 3 follow."""
    data = struct.pack(">I", 10) + b"abc"
    with pytest.raises(EOFError):
        reader(data).read_utf8()


# ---------------------------------------------------------------------------
# read_f64  (Qt float-as-double quirk)
# ---------------------------------------------------------------------------

F64_CASES = [
    {"input": f64(0.0), "expected": 0.0},
    {"input": f64(1.0), "expected": 1.0},
    {"input": f64(-1.0), "expected": -1.0},
    {"input": f64(-12.5), "expected": -12.5},  # typical FT8 SNR
    {"input": f64(0.1), "expected": 0.1},
    {"input": f64(math.inf), "expected": math.inf},
    {"input": f64(-math.inf), "expected": -math.inf},
]


@pytest.mark.parametrize("case", F64_CASES)
def test_read_f64(case):
    assert reader(case["input"]).read_f64() == case["expected"]


def test_read_f64_nan():
    """NaN != NaN, so use math.isnan."""
    result = reader(f64(math.nan)).read_f64()
    assert math.isnan(result)


def test_read_f64_truncated():
    with pytest.raises(EOFError):
        reader(b"\x00\x00\x00\x00").read_f64()


# ---------------------------------------------------------------------------
# Multi-field sequential reads (integration smoke test)
# ---------------------------------------------------------------------------


def test_sequential_reads_heartbeat():
    """
    Simulate the fixed portion of a WSJT-X HEARTBEAT packet (type 0):
      magic   u32  = 0xADBCCB AD
      schema  u32  = 2
      type    u32  = 0
      id      utf8 = "WSJT-X"
      max_schema u32 = 3
    """
    magic = 0xADBCCBAD
    data = u32(magic) + u32(2) + u32(0) + qt_string("WSJT-X") + u32(3)
    r = reader(data)
    assert r.read_u32() == magic
    assert r.read_u32() == 2
    assert r.read_u32() == 0
    assert r.read_utf8() == "WSJT-X"
    assert r.read_u32() == 3
    r.assert_empty()


def test_assert_empty_raises():
    """assert_empty should raise when bytes remain."""
    r = reader(b"\x01\x02")
    r.read_u8()
    with pytest.raises(ValueError, match="unconsumed"):
        r.assert_empty()


def test_assert_empty_passes():
    r = reader(b"\x2a")
    assert r.read_u8() == 42
    r.assert_empty()  # no exception
