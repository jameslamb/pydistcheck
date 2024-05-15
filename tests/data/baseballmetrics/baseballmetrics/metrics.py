import ctypes

from baseballmetrics._shared_lib import _LIB


def batting_average(hits: int, at_bats: int) -> float:
    ret = ctypes.c_double(0.0)
    _LIB.BattingAverage(
        ctypes.c_int32(hits), ctypes.c_int32(at_bats), ctypes.byref(ret)
    )
    return ret.value
