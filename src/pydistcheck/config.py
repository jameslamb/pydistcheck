"""
Manages configuration of ``pydistcheck` CLI, including:

  * validating configuration values
  * updating configuuration from files
"""
import os
from dataclasses import dataclass
from typing import Any, Dict

from pydistcheck._compat import tomllib

# putting this in a module-level set to save on the cost of re-computing it inside methods
# in `_Config` that validate configuration.
#
# unit tests confirm that it matches the `_Config` class, so it shouldn't ever drift from that class
_ALLOWED_CONFIG_VALUES = {
    "ignore",
    "inspect",
    "max_allowed_files",
    "max_allowed_size_compressed",
    "max_allowed_size_uncompressed",
    "unexpected_directory_patterns",
    "unexpected_file_patterns",
}

_UNEXPECTED_DIRECTORIES = [
    "*/.appveyor",
    "*/.binder",
    "*/.circleci",
    "*/.git",
    "*/.github",
    "*/.idea",
    "*/.pytest_cache",
    "*/.mypy_cache",
]

_UNEXPECTED_FILES = [
    "*/appveyor.yml",
    "*/.appveyor.yml",
    "*/azure-pipelines.yml",
    "*/.azure-pipelines.yml",
    "*/.cirrus.star",
    "*/.cirrus.yml",
    "*/codecov.yml",
    "*/.codecov.yml",
    "*/.DS_Store",
    "*/.gitignore",
    "*/.gitpod.yml",
    "*/.hadolint.yaml",
    "*/.readthedocs.yaml",
    "*/.travis.yml",
    "*/vsts-ci.yml",
    "*/.vsts-ci.yml",
]


@dataclass
class _Config:
    ignore: str = ""
    inspect: bool = False
    max_allowed_files: int = 2000
    max_allowed_size_compressed: str = "50M"
    max_allowed_size_uncompressed: str = "75M"
    unexpected_directory_patterns: str = ",".join(_UNEXPECTED_DIRECTORIES)
    unexpected_file_patterns: str = ",".join(_UNEXPECTED_FILES)

    def __setattr__(self, name: str, value: Any) -> None:
        attr_name = name.replace("-", "_")
        if attr_name not in _ALLOWED_CONFIG_VALUES:
            raise ValueError(f"Configuration value '{name}' is not recognized by pydistcheck")
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

        # list-like stuff in TOML is expected to be a comma-delimited string when passed as
        # a command-line argument
        patch_dict: Dict[str, Any] = {}
        for k, v in tool_options.items():
            if isinstance(v, list):
                patch_dict[k] = ",".join(v)
        tool_options.update(patch_dict)
        self.update_from_dict(tool_options)
        return self
