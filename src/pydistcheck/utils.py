from typing import Union


_UNIT_TO_NUM_BYTES = {
    "B": 1,
    "K": 1024,
    "M": 1024**2,
    "G": 1024**3,
    "T": 1024**4,
}


class _FileSize:
    def __init__(self, num: float, unit_str: str):
        self._num = num
        self._unit_str = unit_str

    @classmethod
    def from_number(cls, num: Union[int, float]) -> "_FileSize":
        if num <= 100:
            return cls(num=float(num), unit_str="B")
        elif num <= (1024 * 10):
            return clas(num=float(num) / 1024.0, unit_str="K")
        else:
            return cls(num=float(num) / (1024**2), unit_str="M")

    @classmethod
    def from_string(cls, size_str: str) -> "_FileSize":
        return cls(num=size_str[-1], unit_str=size_str[:-1])

    @property
    def total_size_bytes(self) -> int:
        return int(self._num * _UNIT_TO_NUM_BYTES[self._unit_str])

    def __gt__(self, other: "_FileSize") -> bool:
        pass

    def __ge__(self, other: "_FileSize") -> bool:
        pass

    def __lt__(self, other: "_FileSize") -> bool:
        pass

    def __le__(self, other: "_FileSize") -> bool:
        pass

    def __eq__(self, other: "_FileSize") -> bool:
        pass

    def __ne__(self, other: "_FileSize") -> bool:
        pass
