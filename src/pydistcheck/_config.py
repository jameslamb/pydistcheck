"""
Manages configuration of ``pydistcheck` CLI, including:

  * validating configuration values
  * updating configuuration from files
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, Sequence

from ._compat import tomllib

# putting this in a module-level set to save on the cost of re-computing it inside methods
# in `_Config` that validate configuration.
#
# unit tests confirm that it matches the `_Config` class, so it shouldn't ever drift from that class
_ALLOWED_CONFIG_VALUES = {
    "expected_directories",
    "expected_files",
    "ignore",
    "inspect",
    "max_allowed_files",
    "max_allowed_size_compressed",
    "max_allowed_size_uncompressed",
    "max_path_length",
    "output_file_size_precision",
    "output_file_size_unit",
    "select",
}

_EXPECTED_DIRECTORIES = (
    "!*/.appveyor",
    "!*/.binder",
    "!*/.circleci",
    "!*/.git",
    "!*/.github",
    "!*/.idea",
    "!*/.pytest_cache",
    "!*/.mypy_cache",
)

_EXPECTED_FILES = (
    "!*/appveyor.yml",
    "!*/.appveyor.yml",
    "!*/azure-pipelines.yml",
    "!*/.azure-pipelines.yml",
    "!*/.cirrus.star",
    "!*/.cirrus.yml",
    "!*/codecov.yml",
    "!*/.codecov.yml",
    "!*/.DS_Store",
    "!*/.gitignore",
    "!*/.gitpod.yml",
    "!*/.hadolint.yaml",
    "!*/.lycheecache",
    "!*/.lycheeignore",
    "!*/.readthedocs.yaml",
    "!*/.travis.yml",
    "!*/vsts-ci.yml",
    "!*/.vsts-ci.yml",
)


@dataclass
class _Config:
    expected_directories: Sequence[str] = _EXPECTED_DIRECTORIES
    expected_files: Sequence[str] = _EXPECTED_FILES
    ignore: Sequence[str] = ()
    inspect: bool = False
    max_allowed_files: int = 2000
    max_allowed_size_compressed: str = "50M"
    max_allowed_size_uncompressed: str = "75M"
    max_path_length: int = 200
    output_file_size_precision: int = 3
    output_file_size_unit: str = "auto"
    select: Sequence[str] = ()

    def __setattr__(self, name: str, value: Any) -> None:
        attr_name = name.replace("-", "_")
        if attr_name not in _ALLOWED_CONFIG_VALUES:
            raise ValueError(
                f"Configuration value '{name}' is not recognized by pydistcheck"
            )
        object.__setattr__(self, attr_name, value)

    def update_from_dict(self, input_dict: Dict[str, Any]) -> "_Config":
        for k, v in input_dict.items():
            setattr(self, k, v)
        return self

    def update_from_toml(self, toml_file: str) -> "_Config":
        if not os.path.exists(toml_file):
            return self

        tool_options: Dict[str, Any] = {}
        with open(toml_file, "rb") as f:
            config_dict = tomllib.load(f)
            tool_options = config_dict.get("tool", {}).get("pydistcheck", {})

        self.update_from_dict(tool_options)
        return self
