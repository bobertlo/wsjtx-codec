"""
test_packet.py — end-to-end decode_packet tests.
"""

import struct

import pytest

from wsjtx_codec.packet import (
    HeartbeatPacket,
    MalformedPacket,
    UnknownMessageType,
    UnsupportedSchemaVersion,
    decode_packet,
)
from tests.qdatastream_helpers import reader, u32

MAGIC = struct.pack(">I", 0xADBCCBDA)


def full_packet(schema: int, type_: int, body: bytes) -> bytes:
    return MAGIC + u32(schema) + u32(type_) + body


PACKET_CASES = [
    {
        "input": bytes.fromhex(
            "adbccbda00000002000000000000000657534a542d580000000300000005322e372e3000000000"
        ),
        "expected": HeartbeatPacket(
            schema=2, type=0, id="WSJT-X", max_schema=3, version="2.7.0", revision=""
        ),
    },
]


@pytest.mark.parametrize("case", PACKET_CASES)
def test_decode_packet(case):
    out = decode_packet(reader(case["input"]))
    assert out == case["expected"]


def test_decode_packet_bad_magic():
    with pytest.raises(MalformedPacket):
        decode_packet(reader(b"\x00\x00\x00\x00" + u32(2) + u32(0)))


def test_decode_packet_truncated():
    with pytest.raises(MalformedPacket):
        decode_packet(reader(MAGIC[:2]))


def test_decode_packet_body_truncated():
    with pytest.raises(MalformedPacket):
        decode_packet(reader(full_packet(2, 0, b"\x00\x00")))


def test_decode_packet_unknown_type():
    with pytest.raises(UnknownMessageType) as exc_info:
        decode_packet(reader(full_packet(2, 99, b"")))
    assert exc_info.value.message_type == 99


def test_decode_packet_unsupported_schema():
    with pytest.raises(UnsupportedSchemaVersion) as exc_info:
        decode_packet(reader(full_packet(99, 0, b"")))
    assert exc_info.value.version == 99
