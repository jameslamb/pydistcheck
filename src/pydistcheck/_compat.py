"""
Central location for import stuff used to make the project compatible
with a wide range of dependency versions.
"""

from functools import lru_cache
from typing import Any

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


@lru_cache
def _tf_extractall_has_filter() -> bool:
    """
    tarfile.TarFile.extractall() picked up a new argument ``filter`` in Python 3.12,
    to make extraction more secure.

    That was backported all the way back to Python 3.8 (https://github.com/python/cpython/issues/102950),
    but this function exists to account for older patch versions without the backport.

    On GitHub Actions, for example, 'actions/setup-python' seems to set up
    Python 3.9.13 for CPython on Windows and the backport was in 3.9.17 (https://github.com/python/cpython/pull/104382).

    This can be removed when the oldest support Python here is at least 3.12.
    """
    import inspect  # noqa: PLC0415
    import tarfile  # noqa: PLC0415

    return "filter" in inspect.signature(tarfile.TarFile.extractall).parameters


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
