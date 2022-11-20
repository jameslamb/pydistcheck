"""
Manages configuration of ``pydistcheck` CLI, including:

  * validating configuration values
  * updating configuuration from files
"""
import os
from dataclasses import dataclass
from typing import Any, Dict, Union

from pydistcheck._compat import tomllib

# putting this in a module-level set to save on the cost of re-computing it inside methods
# in `_Config` that validate configuration.
#
# unit tests confirm that it matches the `_Config` class, so it shouldn't ever drift from that class
_ALLOWED_CONFIG_VALUES = {
    "inspect",
    "max_allowed_files",
    "max_allowed_size_compressed",
    "max_allowed_size_uncompressed",
}


@dataclass
class _Config:
    inspect: bool
    max_allowed_files: int
    max_allowed_size_compressed: str
    max_allowed_size_uncompressed: str

    def __setattr__(self, name: str, value: Any) -> None:
        attr_name = name.replace("-", "_")
        if attr_name not in _ALLOWED_CONFIG_VALUES:
            raise ValueError(f"Configuration value '{name}' is not recognized by pydistcheck")
        object.__setattr__(self, attr_name, value)

    def update_from_dict(self, input_dict: Dict[str, Union[bool, float, int, str]]) -> "_Config":
        for k, v in input_dict.items():
            setattr(self, k, v)
        return self

    def update_from_toml(self, toml_file: str) -> "_Config":

        if not os.path.exists(toml_file):
            return self

        tool_options: Dict[str, Union[bool, float, int, str]] = {}
        with open(toml_file, "rb") as f:
            config_dict = tomllib.load(f)
            tool_options = config_dict.get("tool", {}).get("pydistcheck", {})
        self.update_from_dict(tool_options)
        return self
