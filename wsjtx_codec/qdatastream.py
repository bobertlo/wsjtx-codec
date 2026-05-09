"""
QDataStreamReader and QDataStreamWriter — Qt QDataStream wire-format codec.
"""

import struct
from datetime import date, datetime, timedelta, timezone

_JDN_ORDINAL_OFFSET = 1721425  # JDN 1721426 == Python ordinal 1 (0001-01-01)


class QDataStreamReader:
    def __init__(self, data: bytes):
        self.data = memoryview(data)
        self.offset = 0

    def _read(self, n: int) -> memoryview:
        end = self.offset + n
        if end > len(self.data):
            raise EOFError(
                f"need {n} byte(s) at offset {self.offset}, "
                f"but only {len(self.data) - self.offset} remain"
            )
        chunk = self.data[self.offset : end]
        self.offset = end
        return chunk

    def read_u8(self) -> int:
        return struct.unpack_from(">B", self._read(1))[0]

    def read_bool(self) -> bool:
        return self.read_u8() != 0

    def read_u32(self) -> int:
        return struct.unpack_from(">I", self._read(4))[0]

    def read_i32(self) -> int:
        return struct.unpack_from(">i", self._read(4))[0]

    def read_i64(self) -> int:
        return struct.unpack_from(">q", self._read(8))[0]

    def read_u64(self) -> int:
        return struct.unpack_from(">Q", self._read(8))[0]

    def read_f64(self) -> float:
        return struct.unpack_from(">d", self._read(8))[0]

    def read_utf8(self) -> str | None:
        length = self.read_u32()
        if length == 0xFFFFFFFF:
            return None
        if length == 0:
            return ""
        raw = bytes(self._read(length))
        return raw.decode("utf-8")

    def read_qdatetime(self) -> datetime:
        jdn = self.read_i64()
        ms = self.read_u32()
        timespec = self.read_u8()

        d = date.fromordinal(jdn - _JDN_ORDINAL_OFFSET)
        hour = ms // 3600000
        ms %= 3600000
        minute = ms // 60000
        ms %= 60000
        second = ms // 1000
        microsecond = (ms % 1000) * 1000

        if timespec == 0:
            return datetime(d.year, d.month, d.day, hour, minute, second, microsecond)
        if timespec == 1:
            return datetime(
                d.year,
                d.month,
                d.day,
                hour,
                minute,
                second,
                microsecond,
                tzinfo=timezone.utc,
            )
        if timespec == 2:
            tz = timezone(timedelta(seconds=self.read_i32()))
            return datetime(
                d.year, d.month, d.day, hour, minute, second, microsecond, tzinfo=tz
            )
        raise ValueError(f"unsupported QDateTime timespec {timespec}")

    def remaining(self) -> int:
        return len(self.data) - self.offset

    def assert_empty(self) -> None:
        if self.remaining():
            raise ValueError(
                f"{self.remaining()} unconsumed byte(s) at offset {self.offset}"
            )


class QDataStreamWriter:
    def __init__(self) -> None:
        self._buf = bytearray()

    def write_u8(self, n: int) -> None:
        self._buf.extend(struct.pack(">B", n))

    def write_bool(self, b: bool) -> None:
        self._buf.extend(b"\x01" if b else b"\x00")

    def write_u32(self, n: int) -> None:
        self._buf.extend(struct.pack(">I", n))

    def write_i32(self, n: int) -> None:
        self._buf.extend(struct.pack(">i", n))

    def write_i64(self, n: int) -> None:
        self._buf.extend(struct.pack(">q", n))

    def write_u64(self, n: int) -> None:
        self._buf.extend(struct.pack(">Q", n))

    def write_f64(self, n: float) -> None:
        self._buf.extend(struct.pack(">d", n))

    def write_utf8(self, s: str | None) -> None:
        if s is None:
            self._buf.extend(b"\xff\xff\xff\xff")
        else:
            encoded = s.encode("utf-8")
            self._buf.extend(struct.pack(">I", len(encoded)))
            self._buf.extend(encoded)

    def write_qdatetime(self, dt: datetime) -> None:
        jdn = dt.toordinal() + _JDN_ORDINAL_OFFSET
        ms = (
            dt.hour * 3600 + dt.minute * 60 + dt.second
        ) * 1000 + dt.microsecond // 1000
        self.write_i64(jdn)
        self.write_u32(ms)
        if dt.tzinfo is None:
            self.write_u8(0)
        elif dt.tzinfo == timezone.utc:
            self.write_u8(1)
        else:
            self.write_u8(2)
            self.write_i32(int(dt.utcoffset().total_seconds()))

    def getvalue(self) -> bytes:
        return bytes(self._buf)
