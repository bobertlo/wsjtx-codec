"""
WSJT-X packet decoding — header parsing and message dispatch.
"""

from dataclasses import dataclass

from wsjtx_codec.qdatastream import QDataStreamReader

MAGIC = 0xADBCCBDA
HEARTBEAT_TYPE = 0


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
class HeartbeatPacket:
    schema: int
    type: int
    id: str | None
    max_schema: int
    version: str | None
    revision: str | None


def decode_heartbeat(header: Header, r: QDataStreamReader) -> HeartbeatPacket:
    return HeartbeatPacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        max_schema=r.read_u32(),
        version=r.read_utf8(),
        revision=r.read_utf8(),
    )


def decode_packet(r: QDataStreamReader) -> HeartbeatPacket:
    header = decode_header(r)
    if header.type == HEARTBEAT_TYPE:
        return decode_heartbeat(header, r)
    raise ValueError(f"unknown packet type: {header.type}")
