"""
test_packet.py — end-to-end decode_packet tests.
"""

import struct

import pytest

from wsjtx_codec.packet import (
    HeartbeatPacket,
    MalformedPacket,
    StatusPacket,
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
    {
        "input": bytes.fromhex(
            "adbccbda00000002000000010000000657534a542d58"
            "00000000006bf0d0"
            "00000003465438"
            "000000064b4935564843"
            "000000022d38"
            "00000003465438"
            "010000"
            "00000744000009a0"
            "000000064b4630554e4b"
            "00000006454e33344a57"
            "00000004454d3033"
            "00"
            "ffffffff"
            "0000"
            "ffffffffffffffff"
            "00000003473930"
            "000000254351204b4630554e4b20454e3334"
            "2020202020202020202020202020202020202020202020"
        ),
        "expected": StatusPacket(
            schema=2,
            type=1,
            id="WSJT-X",
            dial_freq_hz=7074000,
            mode="FT8",
            dx_call="KI5VHC",
            report="-8",
            tx_mode="FT8",
            tx_enabled=True,
            transmitting=False,
            decoding=False,
            rx_df=1860,
            tx_df=2464,
            de_call="KF0UNK",
            de_grid="EN34JW",
            dx_grid="EM03",
            tx_watchdog=False,
            sub_mode=None,
            fast_mode=False,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name="G90",
            tx_message="CQ KF0UNK EN34                       ",
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
