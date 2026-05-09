"""
WSJT-X packet decoding — header parsing and message dispatch.
"""

from dataclasses import dataclass
from datetime import datetime

from wsjtx_codec.qdatastream import QDataStreamReader

_MAGIC = 0xADBCCBDA
_HEARTBEAT_TYPE = 0
_STATUS_TYPE = 1
_DECODE_TYPE = 2
_CLEAR_TYPE = 3
_QSO_LOGGED_TYPE = 5
_CLOSE_TYPE = 6
_WSPR_TYPE = 10
_LOGGED_ADIF_TYPE = 12
_SUPPORTED_SCHEMAS = {2}


class WsjtxDecodeError(Exception):
    """Base for all decode failures."""


class UnknownMessageType(WsjtxDecodeError):
    """Raised when the packet type field is not recognised."""

    def __init__(self, message_type: int):
        self.message_type = message_type
        super().__init__(f"unknown message type: {message_type}")


class MalformedPacket(WsjtxDecodeError):
    """Buffer is too short, wrong magic, bad UTF-8, etc."""


class UnsupportedSchemaVersion(WsjtxDecodeError):
    """Raised when the schema version in the packet header is not supported."""

    def __init__(self, version: int):
        self.version = version
        super().__init__(f"unsupported schema version: {version}")


@dataclass
class _Header:
    schema: int
    type: int


def _decode_header(r: QDataStreamReader) -> _Header:
    magic = r.read_u32()
    if magic != _MAGIC:
        raise ValueError(f"bad magic number: {magic:#010x}")
    return _Header(schema=r.read_u32(), type=r.read_u32())


@dataclass
class HeartbeatPacket:
    """Periodic keep-alive sent by WSJT-X to announce its presence and version."""

    schema: int
    type: int
    id: str | None
    max_schema: int
    version: str | None
    revision: str | None


def _decode_heartbeat(header: _Header, r: QDataStreamReader) -> HeartbeatPacket:
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
    """Radio and operating state — frequency, mode, callsigns, TX/RX flags."""

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


def _decode_status(header: _Header, r: QDataStreamReader) -> StatusPacket:
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
    """A decoded message received by WSJT-X, with SNR and timing metadata."""

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


def _decode_decode(header: _Header, r: QDataStreamReader) -> DecodePacket:
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
    """Emitted by WSJT-X when prior decodes are discarded from the Band Activity
    window (on user erase or normal shutdown); the receiver should discard all
    buffered decode messages.

    May also be sent *to* a WSJT-X instance to command it to clear one or both
    windows.  In that direction ``window`` is required: 0=Band Activity,
    1=Rx Frequency, 2=Both.  ``window`` is absent (``None``) in the WSJT-X →
    client direction.
    """

    schema: int
    type: int
    id: str | None
    window: int | None = None


def _decode_clear(header: _Header, r: QDataStreamReader) -> ClearPacket:
    return ClearPacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        window=r.read_u8() if r.remaining() > 0 else None,
    )


@dataclass
class ClosePacket:
    """Sent by WSJT-X on shutdown."""

    schema: int
    type: int
    id: str | None


def _decode_close(header: _Header, r: QDataStreamReader) -> ClosePacket:
    return ClosePacket(schema=header.schema, type=header.type, id=r.read_utf8())


@dataclass
class QsoLoggedPacket:
    """Logged QSO record emitted when WSJT-X saves a contact."""

    schema: int
    type: int
    id: str | None
    time_off: datetime
    dx_call: str | None
    dx_grid: str | None
    dial_freq_hz: int
    mode: str | None
    report_sent: str | None
    report_rcvd: str | None
    tx_power: str | None
    comments: str | None
    name: str | None
    time_on: datetime
    operator_call: str | None
    my_call: str | None
    my_grid: str | None
    exchange_sent: str | None
    exchange_rcvd: str | None
    adif_prop_mode: str | None


def _decode_qso_logged(header: _Header, r: QDataStreamReader) -> QsoLoggedPacket:
    return QsoLoggedPacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        time_off=r.read_qdatetime(),
        dx_call=r.read_utf8(),
        dx_grid=r.read_utf8(),
        dial_freq_hz=r.read_u64(),
        mode=r.read_utf8(),
        report_sent=r.read_utf8(),
        report_rcvd=r.read_utf8(),
        tx_power=r.read_utf8(),
        comments=r.read_utf8(),
        name=r.read_utf8(),
        time_on=r.read_qdatetime(),
        operator_call=r.read_utf8(),
        my_call=r.read_utf8(),
        my_grid=r.read_utf8(),
        exchange_sent=r.read_utf8() if r.remaining() > 0 else None,
        exchange_rcvd=r.read_utf8() if r.remaining() > 0 else None,
        adif_prop_mode=r.read_utf8() if r.remaining() > 0 else None,
    )


@dataclass
class WsprPacket:
    """A WSPR decode received by WSJT-X."""

    schema: int
    type: int
    id: str | None
    new: bool
    time_ms: int
    snr: int
    delta_time_s: float
    freq_hz: int
    drift: int
    callsign: str | None
    grid: str | None
    power_dbm: int
    off_air: bool


def _decode_wspr(header: _Header, r: QDataStreamReader) -> WsprPacket:
    return WsprPacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        new=r.read_bool(),
        time_ms=r.read_u32(),
        snr=r.read_i32(),
        delta_time_s=r.read_f64(),
        freq_hz=r.read_u64(),
        drift=r.read_i32(),
        callsign=r.read_utf8(),
        grid=r.read_utf8(),
        power_dbm=r.read_i32(),
        off_air=r.read_bool(),
    )


@dataclass
class LoggedAdifPacket:
    """ADIF-formatted log record emitted when the user accepts the Log QSO dialog.

    ``adif_text`` is a valid ADIF file fragment (fields through ``<EOR>``) that
    can be appended to a standard ADIF header to form a complete single-record
    ADIF file without further parsing.
    """

    schema: int
    type: int
    id: str | None
    adif_text: str | None


def _decode_logged_adif(header: _Header, r: QDataStreamReader) -> LoggedAdifPacket:
    return LoggedAdifPacket(
        schema=header.schema,
        type=header.type,
        id=r.read_utf8(),
        adif_text=r.read_utf8(),
    )


def decode_packet(
    data: bytes,
) -> (
    HeartbeatPacket
    | StatusPacket
    | DecodePacket
    | ClearPacket
    | ClosePacket
    | QsoLoggedPacket
    | WsprPacket
    | LoggedAdifPacket
):
    """Decode a raw WSJT-X UDP packet.

    Raises:
        MalformedPacket: wrong magic, truncated buffer, bad encoding.
        UnsupportedSchemaVersion: schema version not in the supported set.
        UnknownMessageType: packet type field is not recognised.
    """
    r = QDataStreamReader(data)
    try:
        header = _decode_header(r)
        if header.schema not in _SUPPORTED_SCHEMAS:
            raise UnsupportedSchemaVersion(header.schema)
        if header.type == _HEARTBEAT_TYPE:
            return _decode_heartbeat(header, r)
        if header.type == _STATUS_TYPE:
            return _decode_status(header, r)
        if header.type == _DECODE_TYPE:
            return _decode_decode(header, r)
        if header.type == _CLEAR_TYPE:
            return _decode_clear(header, r)
        if header.type == _CLOSE_TYPE:
            return _decode_close(header, r)
        if header.type == _QSO_LOGGED_TYPE:
            return _decode_qso_logged(header, r)
        if header.type == _WSPR_TYPE:
            return _decode_wspr(header, r)
        if header.type == _LOGGED_ADIF_TYPE:
            return _decode_logged_adif(header, r)
        raise UnknownMessageType(header.type)
    except WsjtxDecodeError:
        raise
    except (EOFError, ValueError) as e:
        raise MalformedPacket(str(e)) from e
