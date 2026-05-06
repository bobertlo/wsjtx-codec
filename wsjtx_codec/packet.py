"""
WSJT-X packet decoding — header parsing and message dispatch.
"""

from dataclasses import dataclass

from wsjtx_codec.qdatastream import QDataStreamReader

MAGIC = 0xADBCCBDA
HEARTBEAT_TYPE = 0
STATUS_TYPE = 1
DECODE_TYPE = 2
CLEAR_TYPE = 3
SUPPORTED_SCHEMAS = {2}


class WsjtxDecodeError(Exception):
    """Base for all decode failures."""


class UnknownMessageType(WsjtxDecodeError):
    def __init__(self, message_type: int):
        self.message_type = message_type
        super().__init__(f"unknown message type: {message_type}")


class MalformedPacket(WsjtxDecodeError):
    """Buffer is too short, wrong magic, bad UTF-8, etc."""


class UnsupportedSchemaVersion(WsjtxDecodeError):
    def __init__(self, version: int):
        self.version = version
        super().__init__(f"unsupported schema version: {version}")


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


@dataclass
class StatusPacket:
    schema: int
    type: int
    id: str | None
    dial_freq_hz: int
    mode: str | None
    dx_call: str | None
    report: str | None
    tx_mode: str | None
    tx_enabled: bool
    transmitting: bool
    decoding: bool
    rx_df: int
    tx_df: int
    de_call: str | None
    de_grid: str | None
    dx_grid: str | None
    tx_watchdog: bool
    sub_mode: str | None
    fast_mode: bool
    special_op_mode: int
    freq_tolerance: int | None
    tr_period: int | None
    config_name: str | None
    tx_message: str | None


def decode_status(header: Header, r: QDataStreamReader) -> StatusPacket:
    id = r.read_utf8()
    dial_freq_hz = r.read_u64()
    mode = r.read_utf8()
    dx_call = r.read_utf8()
    report = r.read_utf8()
    tx_mode = r.read_utf8()
    tx_enabled = r.read_bool()
    transmitting = r.read_bool()
    decoding = r.read_bool()
    rx_df = r.read_u32()
    tx_df = r.read_u32()
    de_call = r.read_utf8()
    de_grid = r.read_utf8()
    dx_grid = r.read_utf8()
    tx_watchdog = r.read_bool()
    sub_mode = r.read_utf8()
    fast_mode = r.read_bool()
    special_op_mode = r.read_u8()
    freq_tol_raw = r.read_u32()
    tr_period_raw = r.read_u32()
    config_name = r.read_utf8()
    tx_message = r.read_utf8()

    return StatusPacket(
        schema=header.schema,
        type=header.type,
        id=id,
        dial_freq_hz=dial_freq_hz,
        mode=mode,
        dx_call=dx_call,
        report=report,
        tx_mode=tx_mode,
        tx_enabled=tx_enabled,
        transmitting=transmitting,
        decoding=decoding,
        rx_df=rx_df,
        tx_df=tx_df,
        de_call=de_call,
        de_grid=de_grid,
        dx_grid=dx_grid,
        tx_watchdog=tx_watchdog,
        sub_mode=sub_mode,
        fast_mode=fast_mode,
        special_op_mode=special_op_mode,
        freq_tolerance=None if freq_tol_raw == 0xFFFFFFFF else freq_tol_raw,
        tr_period=None if tr_period_raw == 0xFFFFFFFF else tr_period_raw,
        config_name=config_name,
        tx_message=tx_message,
    )


@dataclass
class DecodePacket:
    schema: int
    type: int
    id: str | None
    new: bool
    time_ms: int
    snr: int
    delta_time_s: float
    delta_freq_hz: int
    mode: str | None
    message: str | None
    low_confidence: bool
    off_air: bool


def decode_decode(header: Header, r: QDataStreamReader) -> DecodePacket:
    return DecodePacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        new=r.read_bool(),
        time_ms=r.read_u32(),
        snr=r.read_i32(),
        delta_time_s=r.read_f64(),
        delta_freq_hz=r.read_u32(),
        mode=r.read_utf8(),
        message=r.read_utf8(),
        low_confidence=r.read_bool(),
        off_air=r.read_bool(),
    )


@dataclass
class ClearPacket:
    schema: int
    type: int
    id: str | None


def decode_clear(header: Header, r: QDataStreamReader) -> ClearPacket:
    return ClearPacket(schema=header.schema, type=header.type, id=r.read_utf8())


def decode_packet(
    r: QDataStreamReader,
) -> HeartbeatPacket | StatusPacket | DecodePacket | ClearPacket:
    try:
        header = decode_header(r)
        if header.schema not in SUPPORTED_SCHEMAS:
            raise UnsupportedSchemaVersion(header.schema)
        if header.type == HEARTBEAT_TYPE:
            return decode_heartbeat(header, r)
        if header.type == STATUS_TYPE:
            return decode_status(header, r)
        if header.type == DECODE_TYPE:
            return decode_decode(header, r)
        if header.type == CLEAR_TYPE:
            return decode_clear(header, r)
        raise UnknownMessageType(header.type)
    except WsjtxDecodeError:
        raise
    except (EOFError, ValueError) as e:
        raise MalformedPacket(str(e)) from e
