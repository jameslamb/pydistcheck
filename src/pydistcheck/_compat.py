"""
Central location for import stuff used to make the project compatible
with a wide range of dependency versions.
"""

import re
import sysconfig
from functools import lru_cache
from typing import Any

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@lru_cache
def _py_major_minor() -> tuple[int, int]:
    python_major, python_minor, *_ = sysconfig.get_python_version().split(".")
    # handle versions like '3.15t'
    python_minor = re.sub("[^0-9.]+", "", python_minor)
    return int(python_major), int(python_minor)


@lru_cache
def _py_gt_312() -> bool:
    python_major, python_minor = _py_major_minor()
    return python_major >= 3 and python_minor >= 12


def _import_zstandard() -> Any:  # pragma: no cover
    try:
        import zstandard  # noqa: PLC0415

        return zstandard
    except ModuleNotFoundError as err:
        err_msg = (
            "Checking zstd-compressed files requires the 'zstandard' library. "
            "Install it with e.g. 'pip install zstandard' or 'conda install -c conda-forge zstandard'."
        )
        raise ModuleNotFoundError(err_msg) from err


__all__ = ["_import_zstandard", "tomllib"]
