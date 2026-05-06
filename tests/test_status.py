"""
test_status.py — pytest harness for WSJT-X status packet decoding.
"""

import pytest

from wsjtx_codec.packet import Header, StatusPacket, decode_status
from tests.qdatastream_helpers import bool_byte, qt_string, reader, u32, u64

DUMMY_HEADER = Header(schema=2, type=1)


def status_bytes(
    id: str | None,
    dial_freq_hz: int,
    mode: str | None,
    dx_call: str | None,
    report: str | None,
    tx_mode: str | None,
    tx_enabled: bool,
    transmitting: bool,
    decoding: bool,
    rx_df: int,
    tx_df: int,
    de_call: str | None,
    de_grid: str | None,
    dx_grid: str | None,
    tx_watchdog: bool,
    sub_mode: str | None,
    fast_mode: bool,
    special_op_mode: int,
    freq_tolerance: int | None,
    tr_period: int | None,
    config_name: str | None,
    tx_message: str | None,
) -> bytes:
    ft_wire = 0xFFFFFFFF if freq_tolerance is None else freq_tolerance
    tp_wire = 0xFFFFFFFF if tr_period is None else tr_period
    return (
        qt_string(id)
        + u64(dial_freq_hz)
        + qt_string(mode)
        + qt_string(dx_call)
        + qt_string(report)
        + qt_string(tx_mode)
        + bool_byte(tx_enabled)
        + bool_byte(transmitting)
        + bool_byte(decoding)
        + u32(rx_df)
        + u32(tx_df)
        + qt_string(de_call)
        + qt_string(de_grid)
        + qt_string(dx_grid)
        + bool_byte(tx_watchdog)
        + qt_string(sub_mode)
        + bool_byte(fast_mode)
        + bytes([special_op_mode])
        + u32(ft_wire)
        + u32(tp_wire)
        + qt_string(config_name)
        + qt_string(tx_message)
    )


STATUS_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex(
            "0000000657534a542d5800000000006bf0d0"
            "00000003465438"
            "000000064b4935564843"
            "000000022d38"
            "00000003465438"
            "01"
            "00"
            "00"
            "00000744"
            "000009a0"
            "000000064b4630554e4b"
            "00000006454e33344a57"
            "00000004454d3033"
            "00"
            "ffffffff"
            "00"
            "00"
            "ffffffff"
            "ffffffff"
            "00000003473930"
            "000000254351204b4630554e4b20454e3334"
            "2020202020202020202020202020202020202020202020"
        ),
        "header": DUMMY_HEADER,
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
        "remaining": 0,
    },
    # All nullable strings are None
    {
        "input": status_bytes(
            id="TEST",
            dial_freq_hz=14074000,
            mode="FT8",
            dx_call=None,
            report=None,
            tx_mode="FT8",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=1500,
            tx_df=1500,
            de_call=None,
            de_grid=None,
            dx_grid=None,
            tx_watchdog=False,
            sub_mode=None,
            fast_mode=False,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name=None,
            tx_message=None,
        ),
        "header": DUMMY_HEADER,
        "expected": StatusPacket(
            schema=2,
            type=1,
            id="TEST",
            dial_freq_hz=14074000,
            mode="FT8",
            dx_call=None,
            report=None,
            tx_mode="FT8",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=1500,
            tx_df=1500,
            de_call=None,
            de_grid=None,
            dx_grid=None,
            tx_watchdog=False,
            sub_mode=None,
            fast_mode=False,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name=None,
            tx_message=None,
        ),
    },
    # All booleans True
    {
        "input": status_bytes(
            id="W1AW",
            dial_freq_hz=7074000,
            mode="FT8",
            dx_call="VK2ABC",
            report="+05",
            tx_mode="FT8",
            tx_enabled=True,
            transmitting=True,
            decoding=True,
            rx_df=1000,
            tx_df=1000,
            de_call="W1AW",
            de_grid="FN31",
            dx_grid="QF56",
            tx_watchdog=True,
            sub_mode=None,
            fast_mode=True,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name="Default",
            tx_message=None,
        ),
        "header": DUMMY_HEADER,
        "expected": StatusPacket(
            schema=2,
            type=1,
            id="W1AW",
            dial_freq_hz=7074000,
            mode="FT8",
            dx_call="VK2ABC",
            report="+05",
            tx_mode="FT8",
            tx_enabled=True,
            transmitting=True,
            decoding=True,
            rx_df=1000,
            tx_df=1000,
            de_call="W1AW",
            de_grid="FN31",
            dx_grid="QF56",
            tx_watchdog=True,
            sub_mode=None,
            fast_mode=True,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name="Default",
            tx_message=None,
        ),
    },
    # Non-zero special_op_mode (FOX=6), non-None freq_tolerance and tr_period
    {
        "input": status_bytes(
            id="WSJT-X",
            dial_freq_hz=50313000,
            mode="FT8",
            dx_call=None,
            report=None,
            tx_mode="FT8",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=1500,
            tx_df=1500,
            de_call="N0FOX",
            de_grid="EM48",
            dx_grid=None,
            tx_watchdog=False,
            sub_mode=None,
            fast_mode=False,
            special_op_mode=6,
            freq_tolerance=10,
            tr_period=15,
            config_name="FOX",
            tx_message=None,
        ),
        "header": DUMMY_HEADER,
        "expected": StatusPacket(
            schema=2,
            type=1,
            id="WSJT-X",
            dial_freq_hz=50313000,
            mode="FT8",
            dx_call=None,
            report=None,
            tx_mode="FT8",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=1500,
            tx_df=1500,
            de_call="N0FOX",
            de_grid="EM48",
            dx_grid=None,
            tx_watchdog=False,
            sub_mode=None,
            fast_mode=False,
            special_op_mode=6,
            freq_tolerance=10,
            tr_period=15,
            config_name="FOX",
            tx_message=None,
        ),
    },
    # Empty strings (not None) for optional fields
    {
        "input": status_bytes(
            id="WSJT-X",
            dial_freq_hz=3573000,
            mode="FT4",
            dx_call="",
            report="",
            tx_mode="FT4",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=700,
            tx_df=700,
            de_call="K0ABC",
            de_grid="",
            dx_grid="",
            tx_watchdog=False,
            sub_mode="",
            fast_mode=False,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name="",
            tx_message="",
        ),
        "header": DUMMY_HEADER,
        "expected": StatusPacket(
            schema=2,
            type=1,
            id="WSJT-X",
            dial_freq_hz=3573000,
            mode="FT4",
            dx_call="",
            report="",
            tx_mode="FT4",
            tx_enabled=False,
            transmitting=False,
            decoding=False,
            rx_df=700,
            tx_df=700,
            de_call="K0ABC",
            de_grid="",
            dx_grid="",
            tx_watchdog=False,
            sub_mode="",
            fast_mode=False,
            special_op_mode=0,
            freq_tolerance=None,
            tr_period=None,
            config_name="",
            tx_message="",
        ),
    },
]


@pytest.mark.parametrize("case", STATUS_CASES)
def test_decode_status(case):
    r = reader(case["input"])
    out = decode_status(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_status_truncated_in_dial_freq():
    with pytest.raises(EOFError):
        decode_status(DUMMY_HEADER, reader(qt_string("WSJT-X") + b"\x00\x00"))


def test_decode_status_truncated_in_booleans():
    # 10 (id) + 8 (dial_freq) + 7 (mode) + 4 (dx_call=None) + 4 (report=None)
    # + 7 (tx_mode) + 1 (tx_enabled) = 41 bytes; next read for 'transmitting' will underflow
    with pytest.raises(EOFError):
        decode_status(
            DUMMY_HEADER,
            reader(
                qt_string("WSJT-X")
                + u64(7074000)
                + qt_string("FT8")
                + qt_string(None)
                + qt_string(None)
                + qt_string("FT8")
                + b"\x01"
            ),
        )
