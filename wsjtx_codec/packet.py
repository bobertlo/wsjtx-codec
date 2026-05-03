"""
WSJT-X packet decoding — header parsing and message dispatch.
"""

from dataclasses import dataclass

from wsjtx_codec.qdatastream import QDataStreamReader

MAGIC = 0xADBCCBDA


@dataclass
class Header:
    schema: int
    type: int


def decode_header(r: QDataStreamReader) -> Header:
    magic = r.read_u32()
    if magic != MAGIC:
        raise ValueError(f"bad magic number: {magic:#010x}")
    return Header(schema=r.read_u32(), type=r.read_u32())


@dataclass
class Heartbeat:
    id: str | None
    max_schema: int
    version: str | None
    revision: str | None


def decode_heartbeat(r: QDataStreamReader) -> Heartbeat:
    return Heartbeat(
        id=r.read_utf8(),
        max_schema=r.read_u32(),
        version=r.read_utf8(),
        revision=r.read_utf8(),
    )
