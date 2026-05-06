"""
test_qso_logged.py — pytest harness for WSJT-X QSO logged packet decoding.
"""

from datetime import datetime, timezone

import pytest

from wsjtx_codec.packet import Header, QsoLoggedPacket, decode_qso_logged
from tests.qdatastream_helpers import (
    qdatetime_utc,
    qt_string,
    reader,
    u64,
)


DUMMY_HEADER = Header(schema=2, type=5)

# Sentinel meaning "omit this field from the packet bytes entirely"
_ABSENT = object()


def qso_logged_bytes(
    id,
    time_off,
    dx_call,
    dx_grid,
    dial_freq_hz,
    mode,
    report_sent,
    report_rcvd,
    tx_power,
    comments,
    name,
    time_on,
    operator_call,
    my_call,
    my_grid,
    exchange_sent=_ABSENT,
    exchange_rcvd=_ABSENT,
    adif_prop_mode=_ABSENT,
) -> bytes:
    base = (
        qt_string(id)
        + qdatetime_utc(time_off)
        + qt_string(dx_call)
        + qt_string(dx_grid)
        + u64(dial_freq_hz)
        + qt_string(mode)
        + qt_string(report_sent)
        + qt_string(report_rcvd)
        + qt_string(tx_power)
        + qt_string(comments)
        + qt_string(name)
        + qdatetime_utc(time_on)
        + qt_string(operator_call)
        + qt_string(my_call)
        + qt_string(my_grid)
    )
    if exchange_sent is not _ABSENT:
        base += qt_string(exchange_sent)
    if exchange_rcvd is not _ABSENT:
        base += qt_string(exchange_rcvd)
    if adif_prop_mode is not _ABSENT:
        base += qt_string(adif_prop_mode)
    return base


_TIME_OFF = datetime(2026, 4, 29, 4, 49, 15, 116000, tzinfo=timezone.utc)
_TIME_ON = datetime(2026, 4, 29, 4, 48, 15, 998000, tzinfo=timezone.utc)

QSO_LOGGED_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex(
            "0000000657534a542d58"
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
        "header": DUMMY_HEADER,
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id="WSJT-X",
            time_off=_TIME_OFF,
            dx_call="N5VAN",
            dx_grid="DN91",
            dial_freq_hz=7076464,
            mode="FT8",
            report_sent="-10",
            report_rcvd="-22",
            tx_power="20W",
            comments="",
            name="",
            time_on=_TIME_ON,
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
            exchange_sent="",
            exchange_rcvd="",
            adif_prop_mode=None,
        ),
        "remaining": 0,
    },
    # No optional trailing fields — exchange_sent/rcvd/adif_prop_mode absent
    {
        "input": qso_logged_bytes(
            id="WSJT-X",
            time_off=_TIME_OFF,
            dx_call="W1AW",
            dx_grid="FN31",
            dial_freq_hz=14074000,
            mode="FT8",
            report_sent="+02",
            report_rcvd="-05",
            tx_power="100W",
            comments="",
            name="",
            time_on=_TIME_ON,
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
        ),
        "header": DUMMY_HEADER,
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id="WSJT-X",
            time_off=_TIME_OFF,
            dx_call="W1AW",
            dx_grid="FN31",
            dial_freq_hz=14074000,
            mode="FT8",
            report_sent="+02",
            report_rcvd="-05",
            tx_power="100W",
            comments="",
            name="",
            time_on=_TIME_ON,
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
            exchange_sent=None,
            exchange_rcvd=None,
            adif_prop_mode=None,
        ),
    },
    # Only exchange fields present, adif_prop_mode absent
    {
        "input": qso_logged_bytes(
            id="WSJT-X",
            time_off=_TIME_OFF,
            dx_call="VK2ABC",
            dx_grid="QF56",
            dial_freq_hz=7074000,
            mode="FT8",
            report_sent="-15",
            report_rcvd="-10",
            tx_power="50W",
            comments="",
            name="",
            time_on=_TIME_ON,
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
            exchange_sent="001",
            exchange_rcvd="042",
        ),
        "header": DUMMY_HEADER,
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id="WSJT-X",
            time_off=_TIME_OFF,
            dx_call="VK2ABC",
            dx_grid="QF56",
            dial_freq_hz=7074000,
            mode="FT8",
            report_sent="-15",
            report_rcvd="-10",
            tx_power="50W",
            comments="",
            name="",
            time_on=_TIME_ON,
            operator_call="",
            my_call="KF0UNK",
            my_grid="EN34JW",
            exchange_sent="001",
            exchange_rcvd="042",
            adif_prop_mode=None,
        ),
    },
    # All nullable strings as None (null utf8 sentinel)
    {
        "input": qso_logged_bytes(
            id=None,
            time_off=_TIME_OFF,
            dx_call=None,
            dx_grid=None,
            dial_freq_hz=0,
            mode=None,
            report_sent=None,
            report_rcvd=None,
            tx_power=None,
            comments=None,
            name=None,
            time_on=_TIME_ON,
            operator_call=None,
            my_call=None,
            my_grid=None,
            exchange_sent=None,
            exchange_rcvd=None,
            adif_prop_mode=None,
        ),
        "header": DUMMY_HEADER,
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id=None,
            time_off=_TIME_OFF,
            dx_call=None,
            dx_grid=None,
            dial_freq_hz=0,
            mode=None,
            report_sent=None,
            report_rcvd=None,
            tx_power=None,
            comments=None,
            name=None,
            time_on=_TIME_ON,
            operator_call=None,
            my_call=None,
            my_grid=None,
            exchange_sent=None,
            exchange_rcvd=None,
            adif_prop_mode=None,
        ),
    },
    # Different times with sub-ms precision exercised through qdatetime_utc
    {
        "input": qso_logged_bytes(
            id="test",
            time_off=datetime(2024, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc),
            dx_call="N0TEST",
            dx_grid="EM48",
            dial_freq_hz=50313000,
            mode="FT8",
            report_sent="+10",
            report_rcvd="+05",
            tx_power="5W",
            comments="test",
            name="Bob",
            time_on=datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
            operator_call="N0OPR",
            my_call="W0TEST",
            my_grid="EM48",
            exchange_sent="",
            exchange_rcvd="",
            adif_prop_mode="EME",
        ),
        "header": DUMMY_HEADER,
        "expected": QsoLoggedPacket(
            schema=2,
            type=5,
            id="test",
            time_off=datetime(2024, 1, 1, 0, 0, 0, 500000, tzinfo=timezone.utc),
            dx_call="N0TEST",
            dx_grid="EM48",
            dial_freq_hz=50313000,
            mode="FT8",
            report_sent="+10",
            report_rcvd="+05",
            tx_power="5W",
            comments="test",
            name="Bob",
            time_on=datetime(2024, 1, 1, 0, 0, 0, 0, tzinfo=timezone.utc),
            operator_call="N0OPR",
            my_call="W0TEST",
            my_grid="EM48",
            exchange_sent="",
            exchange_rcvd="",
            adif_prop_mode="EME",
        ),
    },
]


@pytest.mark.parametrize("case", QSO_LOGGED_CASES)
def test_decode_qso_logged(case):
    r = reader(case["input"])
    out = decode_qso_logged(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_qso_logged_truncated_in_time_off():
    # id present, then only 4 of the 8 JDN bytes for time_off
    with pytest.raises(EOFError):
        decode_qso_logged(
            DUMMY_HEADER, reader(qt_string("WSJT-X") + b"\x00\x00\x00\x00")
        )


def test_decode_qso_logged_truncated_in_dial_freq():
    # All fields through dx_grid present, then only 4 of the 8 dial_freq_hz bytes
    with pytest.raises(EOFError):
        decode_qso_logged(
            DUMMY_HEADER,
            reader(
                qt_string("WSJT-X")
                + qdatetime_utc(_TIME_OFF)
                + qt_string("N5VAN")
                + qt_string("DN91")
                + b"\x00\x00\x00\x00"
            ),
        )
