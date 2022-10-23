# pylint: disable=unused-import

"""
Central location for weird import stuff used to make the project compatible
with a wide range of dependency versions.
"""

try:
    import tomllib  # type: ignore  # noqa: F401
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore  # noqa: F401
