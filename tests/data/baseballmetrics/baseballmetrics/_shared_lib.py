import ctypes
from pathlib import Path

_LIB = ctypes.cdll.LoadLibrary(
    str(Path(__file__).absolute().parents[1].joinpath("lib/lib_baseballmetrics.so"))
)
