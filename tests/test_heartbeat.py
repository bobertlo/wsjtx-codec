"""
test_packet.py — pytest harness for WSJT-X packet decoding.
"""

import pytest

from wsjtx_codec.packet import Header, HeartbeatPacket, decode_heartbeat
from tests.qdatastream_helpers import reader, u32, qt_string


def heartbeat_bytes(
    id: str | None, max_schema: int, version: str | None, revision: str | None
) -> bytes:
    return qt_string(id) + u32(max_schema) + qt_string(version) + qt_string(revision)


DUMMY_HEADER = Header(schema=2, type=0)

HEARTBEAT_CASES = [
    {
        "input": bytes.fromhex(
            "0000000657534a542d580000000300000005322e322e3200000006306439623936"
        ),
        "header": DUMMY_HEADER,
        "expected": HeartbeatPacket(
            schema=2,
            type=0,
            id="WSJT-X",
            max_schema=3,
            version="2.2.2",
            revision="0d9b96",
        ),
        "remaining": 0,
    },
    {
        "input": heartbeat_bytes("WSJT-X", 2, "2.1.0", "abc123"),
        "header": DUMMY_HEADER,
        "expected": HeartbeatPacket(
            schema=2,
            type=0,
            id="WSJT-X",
            max_schema=2,
            version="2.1.0",
            revision="abc123",
        ),
    },
    {
        "input": heartbeat_bytes("my-client", 3, "1.0.0", "rev1") + b"\xff",
        "header": DUMMY_HEADER,
        "expected": HeartbeatPacket(
            schema=2,
            type=0,
            id="my-client",
            max_schema=3,
            version="1.0.0",
            revision="rev1",
        ),
        "remaining": 1,
    },
]


@pytest.mark.parametrize("case", HEARTBEAT_CASES)
def test_decode_heartbeat(case):
    r = reader(case["input"])
    out = decode_heartbeat(case["header"], r)
    assert out == case["expected"]
    if case.get("remaining") is not None:
        assert r.remaining() == case["remaining"]


def test_decode_heartbeat_truncated_id():
    with pytest.raises(EOFError):
        decode_heartbeat(DUMMY_HEADER, reader(b"\x00\x00"))


def test_decode_heartbeat_truncated_max_schema():
    with pytest.raises(EOFError):
        decode_heartbeat(DUMMY_HEADER, reader(qt_string("WSJT-X") + b"\x00\x00"))
