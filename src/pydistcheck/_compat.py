# pylint: disable=unused-import

"""
Central location for weird import stuff used to make the project compatible
with a wide range of dependency versions.
"""

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
