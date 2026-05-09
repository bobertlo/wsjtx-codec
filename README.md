# wsjtx-codec

Pure-Python decoder for the [WSJT-X](https://physics.princeton.edu/pulsar/k1jt/wsjtx.html) UDP protocol with zero external dependencies.

## Install

```
pip install wsjtx_codec
```

## Usage

```python
from wsjtx_codec import (
    decode_packet,
    StatusPacket,
    DecodePacket,
    WsjtxDecodeError,
)

# raw_bytes is a UDP datagram received from WSJT-X (default port 2237)
try:
    packet = decode_packet(raw_bytes)
except WsjtxDecodeError:
    ...  # malformed, unsupported schema, or unknown type

if isinstance(packet, StatusPacket):
    print(packet.de_call, packet.dial_freq_hz)

if isinstance(packet, DecodePacket):
    print(packet.message, packet.snr)
```

## Packet types

| Type | Description |
|------|-------------|
| `HeartbeatPacket` | Keep-alive; carries client ID and version |
| `StatusPacket` | Radio state: frequency, mode, callsigns, TX/RX flags |
| `DecodePacket` | Received message with SNR, timing, and frequency offset |
| `ClearPacket` | Clears the decode list |
| `ClosePacket` | Sent on WSJT-X shutdown |
| `QsoLoggedPacket` | Logged QSO record |
| `WsprPacket` | WSPR decode result |


## Exceptions

| Exception | Raised when |
|-----------|------------|
| `WsjtxDecodeError` | Base class for all decode failures |
| `MalformedPacket` | Wrong magic, truncated buffer, bad encoding |
| `UnsupportedSchemaVersion` | Schema version not supported (only v2) |
| `UnknownMessageType` | Unrecognised packet type field |

## Protocol reference

- [WSJT-X source — NetworkMessage.hpp](https://sourceforge.net/p/wsjt/wsjtx/ci/master/tree/Network/NetworkMessage.hpp)
