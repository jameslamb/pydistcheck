import ctypes
from pathlib import Path

_LIB = ctypes.cdll.LoadLibrary(
    Path(__file__).absolute().parent.joinpath("lib/lib_baseballmetrics.so")
)
