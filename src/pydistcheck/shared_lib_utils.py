"""
functions used to analyze compiled objects
"""

import os
import re
import subprocess
import zipfile
from tempfile import TemporaryDirectory
from typing import List, Tuple

from pydistcheck.distribution_summary import _FileInfo

_COMMAND_FAILED = "__command_failed__"
_NO_DEBUG_SYMBOLS = "__no_debug_symbols_found__"
_TOOL_NOT_AVAILABLE = "__tool_not_available__"


def _run_command(args: List[str]) -> str:
    try:
        stdout = subprocess.run(args, capture_output=True, check=True).stdout
        return stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        return _COMMAND_FAILED
    except FileNotFoundError:
        return _TOOL_NOT_AVAILABLE


# commands to dump symbol information, and regular expressions which, if they match
# any lines in the output, indicate that debug symbols have been found
# fmt: off
_COMMANDS_TO_PATTERNS = [
    (["dsymutil", "-s"],                           r"\(N_OSO[\t ]+\)"),
    (["objdump", "--all-headers"],                 r"[\t ]+\.debug_line[\t ]+"),
    (["objdump", "--macho", "--all-headers"],      r"[\t ]+\.debug_line[\t ]+"),
    (["objdump", "-W"],                            r"^Contents of the \.debug"),
    (["objdump", "--macho", "-W"],                 r"^Contents of the \.debug"),
    (["objdump", "-g"],                            r"^Contents of the \.debug"),
    (["objdump", "--macho", "-g"],                 r"^Contents of the \.debug"),
    (["llvm-objdump", "--all-headers"],            r"[\t ]+\.debug_line[\t ]+"),
    (["llvm-objdump", "--macho", "--all-headers"], r"[\t ]+\.debug_line[\t ]+"),
    (["llvm-objdump", "-W"],                       r"^Contents of the \.debug"),
    (["llvm-objdump", "--macho", "-W"],            r"^Contents of the \.debug"),
    (["llvm-objdump", "-g"],                       r"^Contents of the \.debug"),
    (["llvm-objdump", "--macho", "-g"],            r"^Contents of the \.debug"),
    (["readelf", "-S"],                            r"[\t ]+\.debug_[a-z]+[\t ]+")
]
# fmt: on


def _look_for_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    for cmd_args, pattern in _COMMANDS_TO_PATTERNS:
        stdout = _run_command(args=[*cmd_args, lib_file])
        contains_debug_symbols = any(bool(re.search(pattern, x)) for x in stdout.split("\n"))
        if contains_debug_symbols:
            return True, " ".join(cmd_args)
    # if you get here, no debug symbols were found by any tools
    return False, _NO_DEBUG_SYMBOLS


def _get_symbols(cmd_args: List[str], lib_file: str) -> str:
    syms = _run_command(args=[*cmd_args, lib_file])
    return "\n".join([line for line in syms.split("\n") if not (" a " in line or "\ta\t" in line)])


def _nm_reports_debug_symbols(tool_name: str, lib_file: str) -> Tuple[bool, str]:
    exported_symbols = _get_symbols(cmd_args=[tool_name], lib_file=lib_file)
    all_symbols = _get_symbols(cmd_args=[tool_name, "--debug-syms"], lib_file=lib_file)
    return exported_symbols != all_symbols, f"{tool_name} --debug-syms"


def _archive_member_has_debug_symbols(archive_file: str, file_info: _FileInfo) -> Tuple[bool, str]:
    with TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            zf.extractall(path=tmp_dir, members=[file_info.name])
        full_path = os.path.join(tmp_dir, file_info.name)

        # test with tools that produce debug symbols that can be matched with a regex
        has_debug_symbols, cmd_str = _look_for_debug_symbols(lib_file=full_path)
        if has_debug_symbols:
            return True, cmd_str

        # "nm"'s test is like "check if the output is different when a flag is supplied",
        # instead of "test if this tool produces output matching this regex",
        # so it runs separately here
        for nm_tool in ["nm", "llvm-nm"]:
            has_debug_symbols, cmd_str = _nm_reports_debug_symbols(
                tool_name=nm_tool,
                lib_file=full_path,
            )
            if has_debug_symbols:
                return True, cmd_str

    # at this point, none of the checks found debug symbols
    return False, cmd_str
