"""
test_logged_adif.py — pytest harness for WSJT-X LoggedAdif packet decoding.
"""

import pytest

from wsjtx_codec.packet import LoggedAdifPacket, _Header, _decode_logged_adif
from tests.qdatastream_helpers import qt_string, reader

DUMMY_HEADER = _Header(schema=2, type=12)

_ADIF_SAMPLE = (
    "<adif_ver:5>3.0.7\n"
    "<programid:6>WSJT-X\n"
    "<EOH>\n"
    "<call:5>K0SWE<band:3>20m<mode:3>FT8<rst_sent:3>-10<rst_rcvd:3>-07<EOR>"
)

LOGGED_ADIF_CASES = [
    # typical full record
    {
        "input": qt_string("WSJT-X") + qt_string(_ADIF_SAMPLE),
        "header": DUMMY_HEADER,
        "expected": LoggedAdifPacket(
            schema=2, type=12, id="WSJT-X", adif_text=_ADIF_SAMPLE
        ),
        "remaining": 0,
    },
    # different client id
    {
        "input": qt_string("my-client") + qt_string(_ADIF_SAMPLE),
        "header": DUMMY_HEADER,
        "expected": LoggedAdifPacket(
            schema=2, type=12, id="my-client", adif_text=_ADIF_SAMPLE
        ),
    },
    # null id
    {
        "input": qt_string(None) + qt_string(_ADIF_SAMPLE),
        "header": DUMMY_HEADER,
        "expected": LoggedAdifPacket(
            schema=2, type=12, id=None, adif_text=_ADIF_SAMPLE
        ),
    },
    # null adif_text
    {
        "input": qt_string("WSJT-X") + qt_string(None),
        "header": DUMMY_HEADER,
        "expected": LoggedAdifPacket(schema=2, type=12, id="WSJT-X", adif_text=None),
    },
    # empty adif_text
    {
        "input": qt_string("WSJT-X") + qt_string(""),
        "header": DUMMY_HEADER,
        "expected": LoggedAdifPacket(schema=2, type=12, id="WSJT-X", adif_text=""),
    },
]


@pytest.mark.parametrize("case", LOGGED_ADIF_CASES)
def test__decode_logged_adif(case):
    r = reader(case["input"])
    out = _decode_logged_adif(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_logged_adif_truncated_id():
    # length prefix says 6 bytes but only 3 present
    with pytest.raises(EOFError):
        _decode_logged_adif(DUMMY_HEADER, reader(b"\x00\x00\x00\x06\x57\x53\x4a"))


def test_decode_logged_adif_missing_adif_text():
    # id present but adif_text field entirely absent
    with pytest.raises(EOFError):
        _decode_logged_adif(DUMMY_HEADER, reader(qt_string("WSJT-X")))
