"""
test_decode.py — pytest harness for WSJT-X decode packet decoding.
"""

import pytest

from wsjtx_codec.packet import DecodePacket, _Header, _decode_decode
from tests.qdatastream_helpers import bool_byte, f64, i32, qt_string, reader, u32


DUMMY_HEADER = _Header(schema=2, type=2)


def decode_bytes(
    id: str | None,
    new: bool,
    time_ms: int,
    snr: int,
    delta_time_s: float,
    delta_freq_hz: int,
    mode: str | None,
    message: str | None,
    low_confidence: bool,
    off_air: bool,
) -> bytes:
    return (
        qt_string(id)
        + bool_byte(new)
        + u32(time_ms)
        + i32(snr)
        + f64(delta_time_s)
        + u32(delta_freq_hz)
        + qt_string(mode)
        + qt_string(message)
        + bool_byte(low_confidence)
        + bool_byte(off_air)
    )


DECODE_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex(
            "0000000657534a542d58"
            "01"
            "010c3fe0"
            "fffffffc"
            "bfe0000000000000"
            "00000744"
            "000000017e"
            "000000114b4630554e4b204b4935564843202d3231"
            "0000"
        ),
        "header": DUMMY_HEADER,
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
        "remaining": 0,
    },
    # Positive SNR, positive delta_time_s
    {
        "input": decode_bytes(
            id="WSJT-X",
            new=True,
            time_ms=0,
            snr=12,
            delta_time_s=1.5,
            delta_freq_hz=500,
            mode="FT8",
            message="CQ DX W1AW FN31",
            low_confidence=False,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": DecodePacket(
            schema=2,
            type=2,
            id="WSJT-X",
            new=True,
            time_ms=0,
            snr=12,
            delta_time_s=1.5,
            delta_freq_hz=500,
            mode="FT8",
            message="CQ DX W1AW FN31",
            low_confidence=False,
            off_air=False,
        ),
    },
    # low_confidence=True, off_air=True
    {
        "input": decode_bytes(
            id="WSJT-X",
            new=True,
            time_ms=3600000,
            snr=-20,
            delta_time_s=0.0,
            delta_freq_hz=2000,
            mode="JT65",
            message="W1AW VK2ABC -15",
            low_confidence=True,
            off_air=True,
        ),
        "header": DUMMY_HEADER,
        "expected": DecodePacket(
            schema=2,
            type=2,
            id="WSJT-X",
            new=True,
            time_ms=3600000,
            snr=-20,
            delta_time_s=0.0,
            delta_freq_hz=2000,
            mode="JT65",
            message="W1AW VK2ABC -15",
            low_confidence=True,
            off_air=True,
        ),
    },
    # mode=None, message=None
    {
        "input": decode_bytes(
            id="my-client",
            new=False,
            time_ms=86399000,
            snr=0,
            delta_time_s=-2.0,
            delta_freq_hz=1200,
            mode=None,
            message=None,
            low_confidence=False,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": DecodePacket(
            schema=2,
            type=2,
            id="my-client",
            new=False,
            time_ms=86399000,
            snr=0,
            delta_time_s=-2.0,
            delta_freq_hz=1200,
            mode=None,
            message=None,
            low_confidence=False,
            off_air=False,
        ),
    },
    # new=False, delta_freq_hz=0
    {
        "input": decode_bytes(
            id="WSJT-X",
            new=False,
            time_ms=57600000,
            snr=-10,
            delta_time_s=0.3,
            delta_freq_hz=0,
            mode="~",
            message="CQ KF0UNK EN34",
            low_confidence=False,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": DecodePacket(
            schema=2,
            type=2,
            id="WSJT-X",
            new=False,
            time_ms=57600000,
            snr=-10,
            delta_time_s=0.3,
            delta_freq_hz=0,
            mode="~",
            message="CQ KF0UNK EN34",
            low_confidence=False,
            off_air=False,
        ),
    },
]


@pytest.mark.parametrize("case", DECODE_CASES)
def test__decode_decode(case):
    r = reader(case["input"])
    out = _decode_decode(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_decode_truncated_in_time_ms():
    # id + new byte present, then only 2 of the 4 time_ms bytes
    with pytest.raises(EOFError):
        _decode_decode(
            DUMMY_HEADER, reader(qt_string("WSJT-X") + bool_byte(True) + b"\x01\x0c")
        )


def test_decode_decode_truncated_in_delta_time_s():
    # All fields through snr present, then only 4 of the 8 delta_time_s bytes
    with pytest.raises(EOFError):
        _decode_decode(
            DUMMY_HEADER,
            reader(
                qt_string("WSJT-X")
                + bool_byte(True)
                + u32(17580000)
                + i32(-4)
                + b"\xbf\xe0\x00\x00"
            ),
        )
