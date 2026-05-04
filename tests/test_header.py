"""
test_packet.py — pytest harness for WSJT-X packet decoding.
"""

import pytest

from wsjtx_codec.packet import MAGIC, Header, decode_header

from tests.qdatastream_helpers import reader, u32


def header_bytes(schema: int, msg_type: int, *, magic: int = MAGIC) -> bytes:
    return u32(magic) + u32(schema) + u32(msg_type)


HEADER_CASES = [
    {"input": header_bytes(2, 0), "expected": Header(schema=2, type=0), "remaining": 0},
    {"input": header_bytes(3, 1), "expected": Header(schema=3, type=1)},
    {"input": header_bytes(2, 5), "expected": Header(schema=2, type=5)},
    {
        "input": header_bytes(2, 0) + b"\xff",
        "expected": Header(schema=2, type=0),
        "remaining": 1,
    },
]


@pytest.mark.parametrize("case", HEADER_CASES)
def test_decode_header(case):
    r = reader(case["input"])
    out = decode_header(r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_header_bad_magic():
    with pytest.raises(ValueError, match="magic"):
        decode_header(reader(header_bytes(2, 0, magic=0xDEADBEEF)))


def test_decode_header_truncated_magic():
    with pytest.raises(EOFError):
        decode_header(reader(b"\xad\xbc\xcb"))


def test_decode_header_truncated_schema():
    with pytest.raises(EOFError):
        decode_header(reader(u32(MAGIC) + b"\x00\x00"))


def test_decode_header_truncated_type():
    with pytest.raises(EOFError):
        decode_header(reader(u32(MAGIC) + u32(2)))
