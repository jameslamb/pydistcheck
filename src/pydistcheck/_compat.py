"""
Central location for weird import stuff used to make the project compatible
with a wide range of dependency versions.
"""

from typing import Any

try:  # pragma: no cover
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]


def _import_zstandard() -> Any:
    try:
        import zstandard

        return zstandard
    except ModuleNotFoundError as err:
        err_msg = (
            "Checking zstd-compressed files requires the 'zstandard' library. "
            "Install it with e.g. 'pip install zstandard' or 'conda install conda-forge::zstandard'."
        )
        raise ModuleNotFoundError(err_msg) from err


__all__ = ["_import_zstandard", "tomllib"]
