"""
test_packet.py — pytest harness for WSJT-X packet decoding.
"""

import struct

import pytest

from wsjtx_codec.packet import MAGIC, Header, Heartbeat, decode_header, decode_heartbeat
from wsjtx_codec.qdatastream import QDataStreamReader


def reader(data: bytes) -> QDataStreamReader:
    return QDataStreamReader(data, version=15)


def u32(n: int) -> bytes:
    return struct.pack(">I", n)


def qt_string(s: str | None) -> bytes:
    if s is None:
        return b"\xff\xff\xff\xff"
    enc = s.encode("utf-8")
    return struct.pack(">I", len(enc)) + enc


def header_bytes(schema: int, msg_type: int, *, magic: int = MAGIC) -> bytes:
    return u32(magic) + u32(schema) + u32(msg_type)


def _run_test_case(case, adapter):
    r = reader(case["input"])
    out = adapter(r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


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
    _run_test_case(case, decode_header)


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


def heartbeat_bytes(
    id: str | None, max_schema: int, version: str | None, revision: str | None
) -> bytes:
    return qt_string(id) + u32(max_schema) + qt_string(version) + qt_string(revision)


HEARTBEAT_CASES = [
    {
        "input": bytes.fromhex(
            "0000000657534a542d580000000300000005322e322e3200000006306439623936"
        ),
        "expected": Heartbeat(
            id="WSJT-X", max_schema=3, version="2.2.2", revision="0d9b96"
        ),
        "remaining": 0,
    },
    {
        "input": heartbeat_bytes("WSJT-X", 2, "2.1.0", "abc123"),
        "expected": Heartbeat(
            id="WSJT-X", max_schema=2, version="2.1.0", revision="abc123"
        ),
    },
    {
        "input": heartbeat_bytes("my-client", 3, "1.0.0", "rev1") + b"\xff",
        "expected": Heartbeat(
            id="my-client", max_schema=3, version="1.0.0", revision="rev1"
        ),
        "remaining": 1,
    },
]


@pytest.mark.parametrize("case", HEARTBEAT_CASES)
def test_decode_heartbeat(case):
    _run_test_case(case, decode_heartbeat)


def test_decode_heartbeat_truncated_id():
    with pytest.raises(EOFError):
        decode_heartbeat(reader(b"\x00\x00"))


def test_decode_heartbeat_truncated_max_schema():
    with pytest.raises(EOFError):
        decode_heartbeat(reader(qt_string("WSJT-X") + b"\x00\x00"))
