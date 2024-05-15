import ctypes
from pathlib import Path
from platform import system

if system() == "Darwin":
    _shlib_ext = "dylib"
else:
    _shlib_ext = "so"

_LIB = ctypes.cdll.LoadLibrary(
    str(
        Path(__file__)
        .absolute()
        .parents[1]
        .joinpath(f"lib/lib_baseballmetrics.{_shlib_ext}")
    )
)
