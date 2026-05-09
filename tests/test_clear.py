"""
test_clear.py — pytest harness for WSJT-X clear packet decoding.
"""

import pytest

from wsjtx_codec.packet import ClearPacket, _Header, _decode_clear
from tests.qdatastream_helpers import qt_string, reader


DUMMY_HEADER = _Header(schema=2, type=3)

CLEAR_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex("0000000657534a542d58"),
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X"),
        "remaining": 0,
    },
    # Different client id
    {
        "input": qt_string("my-client"),
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id="my-client"),
    },
    # id=None (null utf8)
    {
        "input": qt_string(None),
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id=None),
    },
    # id="" (empty utf8)
    {
        "input": qt_string(""),
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id=""),
    },
    # window=0 (clear Band Activity) — client → WSJT-X direction
    {
        "input": qt_string("WSJT-X") + b"\x00",
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X", window=0),
        "remaining": 0,
    },
    # window=1 (clear Rx Frequency)
    {
        "input": qt_string("WSJT-X") + b"\x01",
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X", window=1),
    },
    # window=2 (clear Both windows)
    {
        "input": qt_string("WSJT-X") + b"\x02",
        "header": DUMMY_HEADER,
        "expected": ClearPacket(schema=2, type=3, id="WSJT-X", window=2),
    },
]


@pytest.mark.parametrize("case", CLEAR_CASES)
def test__decode_clear(case):
    r = reader(case["input"])
    out = _decode_clear(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_clear_truncated():
    # 4-byte length prefix present but id bytes cut short
    with pytest.raises(EOFError):
        _decode_clear(DUMMY_HEADER, reader(b"\x00\x00\x00\x06\x57\x53"))
