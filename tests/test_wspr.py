"""
test_wspr.py — pytest harness for WSJT-X WSPR decode packet decoding.
"""

import pytest

from wsjtx_codec.packet import Header, WsprPacket, decode_wspr
from tests.qdatastream_helpers import (
    bool_byte,
    f64,
    i32,
    qt_string,
    reader,
    u32,
    u64,
)


DUMMY_HEADER = Header(schema=2, type=10)


def wspr_bytes(
    id,
    new,
    time_ms,
    snr,
    delta_time_s,
    freq_hz,
    drift,
    callsign,
    grid,
    power_dbm,
    off_air,
) -> bytes:
    return (
        qt_string(id)
        + bool_byte(new)
        + u32(time_ms)
        + i32(snr)
        + f64(delta_time_s)
        + u64(freq_hz)
        + i32(drift)
        + qt_string(callsign)
        + qt_string(grid)
        + i32(power_dbm)
        + bool_byte(off_air)
    )


WSPR_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex(
            "0000000657534a542d58"
            "0100a6a040ffffffe6"
            "0000000000000000"
            "00000000003679ee"
            "00000000"
            "000000054e35435858"
            "00000004454d3132"
            "00000017"
            "00"
        ),
        "header": DUMMY_HEADER,
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
        "remaining": 0,
    },
    # off_air=True
    {
        "input": wspr_bytes(
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
            off_air=True,
        ),
        "header": DUMMY_HEADER,
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
            off_air=True,
        ),
    },
    # Null callsign and grid (utf8 null sentinels)
    {
        "input": wspr_bytes(
            id="WSJT-X",
            new=False,
            time_ms=0,
            snr=0,
            delta_time_s=0.0,
            freq_hz=0,
            drift=0,
            callsign=None,
            grid=None,
            power_dbm=0,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": WsprPacket(
            schema=2,
            type=10,
            id="WSJT-X",
            new=False,
            time_ms=0,
            snr=0,
            delta_time_s=0.0,
            freq_hz=0,
            drift=0,
            callsign=None,
            grid=None,
            power_dbm=0,
            off_air=False,
        ),
    },
    # Positive SNR, non-zero drift
    {
        "input": wspr_bytes(
            id="WSJT-X",
            new=True,
            time_ms=75720000,
            snr=5,
            delta_time_s=1.5,
            freq_hz=14097073,
            drift=2,
            callsign="W1AW",
            grid="FN31",
            power_dbm=37,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": WsprPacket(
            schema=2,
            type=10,
            id="WSJT-X",
            new=True,
            time_ms=75720000,
            snr=5,
            delta_time_s=1.5,
            freq_hz=14097073,
            drift=2,
            callsign="W1AW",
            grid="FN31",
            power_dbm=37,
            off_air=False,
        ),
    },
    # 40m WSPR band
    {
        "input": wspr_bytes(
            id="WSJT-X",
            new=True,
            time_ms=10920000,
            snr=-12,
            delta_time_s=-0.5,
            freq_hz=7040074,
            drift=-1,
            callsign="VK2XAB",
            grid="QF56",
            power_dbm=30,
            off_air=False,
        ),
        "header": DUMMY_HEADER,
        "expected": WsprPacket(
            schema=2,
            type=10,
            id="WSJT-X",
            new=True,
            time_ms=10920000,
            snr=-12,
            delta_time_s=-0.5,
            freq_hz=7040074,
            drift=-1,
            callsign="VK2XAB",
            grid="QF56",
            power_dbm=30,
            off_air=False,
        ),
    },
]


@pytest.mark.parametrize("case", WSPR_CASES)
def test_decode_wspr(case):
    r = reader(case["input"])
    out = decode_wspr(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_wspr_truncated():
    # id + new + time + snr + delta_time_s present, then only 4 of 8 freq_hz bytes
    with pytest.raises(EOFError):
        decode_wspr(
            DUMMY_HEADER,
            reader(
                qt_string("WSJT-X")
                + bool_byte(True)
                + u32(10920000)
                + i32(-26)
                + f64(0.0)
                + b"\x00\x00\x00\x00"
            ),
        )
