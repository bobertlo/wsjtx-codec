"""
test_close.py — pytest harness for WSJT-X close packet decoding.
"""

import pytest

from wsjtx_codec.packet import ClosePacket, Header, decode_close
from tests.qdatastream_helpers import qt_string, reader


DUMMY_HEADER = Header(schema=2, type=6)

CLOSE_CASES = [
    # Real packet body captured from a live WSJT-X instance
    {
        "input": bytes.fromhex("0000000657534a542d58"),
        "header": DUMMY_HEADER,
        "expected": ClosePacket(schema=2, type=6, id="WSJT-X"),
        "remaining": 0,
    },
    # Different client id
    {
        "input": qt_string("my-client"),
        "header": DUMMY_HEADER,
        "expected": ClosePacket(schema=2, type=6, id="my-client"),
    },
    # id=None (null utf8)
    {
        "input": qt_string(None),
        "header": DUMMY_HEADER,
        "expected": ClosePacket(schema=2, type=6, id=None),
    },
    # id="" (empty utf8)
    {
        "input": qt_string(""),
        "header": DUMMY_HEADER,
        "expected": ClosePacket(schema=2, type=6, id=""),
    },
]


@pytest.mark.parametrize("case", CLOSE_CASES)
def test_decode_close(case):
    r = reader(case["input"])
    out = decode_close(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_close_truncated():
    # 4-byte length prefix present but id bytes cut short
    with pytest.raises(EOFError):
        decode_close(DUMMY_HEADER, reader(b"\x00\x00\x00\x06\x57\x53"))
