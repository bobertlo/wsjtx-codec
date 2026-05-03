"""
QDataStreamReader — minimal Qt QDataStream wire-format reader.
"""

import struct
from datetime import date, datetime, timedelta, timezone

_JDN_ORDINAL_OFFSET = 1721425  # JDN 1721426 == Python ordinal 1 (0001-01-01)


class QDataStreamReader:
    def __init__(self, data: bytes, *, version: int):
        self.data = memoryview(data)
        self.offset = 0
        self.version = version

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

        if timespec == 0:
            return datetime(d.year, d.month, d.day, hour, minute, second)
        if timespec == 1:
            return datetime(
                d.year, d.month, d.day, hour, minute, second, tzinfo=timezone.utc
            )
        if timespec == 2:
            tz = timezone(timedelta(seconds=self.read_i32()))
            return datetime(d.year, d.month, d.day, hour, minute, second, tzinfo=tz)
        raise ValueError(f"unsupported QDateTime timespec {timespec}")

    def remaining(self) -> int:
        return len(self.data) - self.offset

    def assert_empty(self) -> None:
        if self.remaining():
            raise ValueError(
                f"{self.remaining()} unconsumed byte(s) at offset {self.offset}"
            )
