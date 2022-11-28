"""
miscellaneous helper classes and functions that are
not specific to package distributions
"""

from typing import Any, Tuple

_UNIT_TO_NUM_BYTES = {"B": 1, "K": 1024, "M": 1024**2, "G": 1024**3}


def _recommend_size_str(num_bytes: int) -> Tuple[float, str]:
    if num_bytes < int(0.1 * 1024):
        return float(num_bytes), "B"
    if num_bytes <= (0.1 * 1024**2):
        return float(num_bytes) / 1024.0, "K"
    if num_bytes <= (0.1 * 1024**3):
        return float(num_bytes) / (1024**2), "M"

    return float(num_bytes) / (1024**3), "G"


class _FileSize:
    def __init__(self, num: float, unit_str: str):
        self._num = num
        self._unit_str = unit_str

    @classmethod
    def from_number(cls, num: int) -> "_FileSize":
        num_bytes, unit_str = _recommend_size_str(num_bytes=num)
        return cls(num=num_bytes, unit_str=unit_str)

    @classmethod
    def from_string(cls, size_str: str) -> "_FileSize":
        return cls(num=float(size_str[:-1]), unit_str=size_str[-1])

    @property
    def total_size_bytes(self) -> int:
        return int(self._num * _UNIT_TO_NUM_BYTES[self._unit_str])

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, type(self)) and self.total_size_bytes == other.total_size_bytes

    def __ge__(self, other: "_FileSize") -> bool:
        return self.total_size_bytes >= other.total_size_bytes

    def __gt__(self, other: "_FileSize") -> bool:
        return self.total_size_bytes > other.total_size_bytes

    def __le__(self, other: "_FileSize") -> bool:
        return self.total_size_bytes <= other.total_size_bytes

    def __lt__(self, other: "_FileSize") -> bool:
        return self.total_size_bytes < other.total_size_bytes

    def __ne__(self, other: Any) -> bool:
        return not self == other

    def __str__(self) -> str:
        num_bytes, unit_str = _recommend_size_str(self.total_size_bytes)
        return f"{round(num_bytes, 1)}{unit_str}"
