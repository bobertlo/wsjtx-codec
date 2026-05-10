"""
test_packet.py — end-to-end decode_packet tests.
"""

import struct
from datetime import datetime, timezone

import pytest

from wsjtx_codec.packet import (
    ClearPacket,
    ClosePacket,
    DecodePacket,
    HeartbeatPacket,
    LoggedAdifPacket,
    MalformedPacket,
    QsoLoggedPacket,
    StatusPacket,
    UnknownMessageType,
    UnsupportedSchemaVersion,
    WsprPacket,
    decode_packet,
)
from tests.qdatastream_helpers import u32

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
    {
        "input": bytes.fromhex(
            "adbccbda00000002000000020000000657534a542d58"
            "01"
            "010c3fe0"
            "fffffffc"
            "bfe0000000000000"
            "00000744"
            "000000017e"
            "000000114b4630554e4b204b4935564843202d3231"
            "0000"
        ),
        "expected": DecodePacket(
            schema=2,
            type=2,
            id="WSJT-X",
            new=True,
            time_ms=17580000,
            snr=-4,
            delta_time_s=-0.5,
            delta_freq_hz=1860,
            mode="~",
            message="KF0UNK KI5VHC -21",
            low_confidence=False,
            off_air=False,
        ),
    },
    {
        "input": bytes.fromhex("adbccbda00000002000000030000000657534a542d58"),
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X"),
    },
    # Clear with window=2 (both windows) — client → WSJT-X direction
    {
        "input": bytes.fromhex("adbccbda00000002000000030000000657534a542d5802"),
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X", window=2),
    },
    {
        "input": bytes.fromhex("adbccbda00000002000000060000000657534a542d58"),
        "expected": ClosePacket(schema=2, type=6, id="WSJT-X"),
    },
    {
        "input": bytes.fromhex(
            "adbccbda00000002000000050000000657534a542d58"
            "0000000000258de80108d16c01"
            "000000054e3556414e"
            "00000004444e3931"
            "00000000006bfa70"
            "00000003465438"
            "000000032d3130"
            "000000032d3232"
            "00000003323057"
            "0000000000000000"
            "0000000000258de80107ea7e01"
            "00000000"
            "000000064b4630554e4b"
            "00000006454e33344a57"
            "00000000"
            "00000000"
            "ffffffff"
        ),
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id="WSJT-X",
            time_off=datetime(2026, 4, 29, 4, 49, 15, 116000, tzinfo=timezone.utc),
            dx_call="N5VAN",
            dx_grid="DN91",
            dial_freq_hz=7076464,
            mode="FT8",
            report_sent="-10",
            report_rcvd="-22",
            tx_power="20W",
            comments="",
            name="",
            time_on=datetime(2026, 4, 29, 4, 48, 15, 998000, tzinfo=timezone.utc),
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
            exchange_sent="",
            exchange_rcvd="",
            adif_prop_mode=None,
        ),
    },
    {
        "input": bytes.fromhex(
            "adbccbda000000020000000c0000000657534a542d58"
            "000001310a3c616469665f7665723a353e332e312e300a"
            "3c70726f6772616d69643a363e57534a542d580a3c454f483e0a"
            "3c63616c6c3a353e4b4e345142203c677269647371756172653a343e454d3736"
            "203c6d6f64653a333e465438203c7273745f73656e743a333e2d3134"
            "203c7273745f726376643a333e2d3034203c71736f5f646174653a383e3230323630353130"
            "203c74696d655f6f6e3a363e313431373030203c71736f5f646174655f6f66663a383e3230323630353130"
            "203c74696d655f6f66663a363e313431383030203c62616e643a333e32306d"
            "203c667265713a393e31342e303736303435"
            "203c73746174696f6e5f63616c6c7369676e3a363e4b4630554e4b"
            "203c6d795f677269647371756172653a363e454e33344a57"
            "203c74785f7077723a333e323057203c454f523e"
        ),
        "expected": LoggedAdifPacket(
            schema=2,
            type=12,
            id="WSJT-X",
            adif_text=(
                "\n<adif_ver:5>3.1.0\n<programid:6>WSJT-X\n<EOH>\n"
                "<call:5>KN4QB <gridsquare:4>EM76 <mode:3>FT8"
                " <rst_sent:3>-14 <rst_rcvd:3>-04"
                " <qso_date:8>20260510 <time_on:6>141700"
                " <qso_date_off:8>20260510 <time_off:6>141800"
                " <band:3>20m <freq:9>14.076045"
                " <station_callsign:6>KF0UNK <my_gridsquare:6>EN34JW"
                " <tx_pwr:3>20W <EOR>"
            ),
        ),
    },
    {
        "input": bytes.fromhex(
            "adbccbda000000020000000a0000000657534a542d58"
            "0100a6a040ffffffe6"
            "0000000000000000"
            "00000000003679ee"
            "00000000"
            "000000054e35435858"
            "00000004454d3132"
            "00000017"
            "00"
        ),
        "expected": WsprPacket(
            schema=2,
            type=10,
            id="WSJT-X",
            new=True,
            time_ms=10920000,
            snr=-26,
            delta_time_s=0.0,
            freq_hz=3570158,
            drift=0,
            callsign="N5CXX",
            grid="EM12",
            power_dbm=23,
            off_air=False,
        ),
    },
]


@pytest.mark.parametrize("case", PACKET_CASES)
def test_decode_packet(case):
    out = decode_packet(case["input"])
    assert out == case["expected"]


def test_decode_packet_bad_magic():
    with pytest.raises(MalformedPacket):
        decode_packet(b"\x00\x00\x00\x00" + u32(2) + u32(0))


def test_decode_packet_truncated():
    with pytest.raises(MalformedPacket):
        decode_packet(MAGIC[:2])


def test_decode_packet_body_truncated():
    with pytest.raises(MalformedPacket):
        decode_packet(full_packet(2, 0, b"\x00\x00"))


def test_decode_packet_unknown_type():
    with pytest.raises(UnknownMessageType) as exc_info:
        decode_packet(full_packet(2, 99, b""))
    assert exc_info.value.message_type == 99


def test_decode_packet_unsupported_schema():
    with pytest.raises(UnsupportedSchemaVersion) as exc_info:
        decode_packet(full_packet(99, 0, b""))
    assert exc_info.value.version == 99
