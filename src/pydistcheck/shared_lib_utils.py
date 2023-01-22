"""
functions used to analyze compiled objects
"""

import os
import re
import subprocess
import sys
import zipfile
from tempfile import TemporaryDirectory
from typing import List, Optional, Tuple

LIB_FILE = sys.argv[1]

_COMMAND_FAILED = "__command_failed__"
_TOOL_NOT_AVAILABLE = "__tool_not_available__"


def _run_command(args: List[str]) -> Optional[str]:
    try:
        stdout = subprocess.run(args, capture_output=True, check=True).stdout
        return stdout.decode("utf-8")
    except subprocess.CalledProcessError:
        return _COMMAND_FAILED
    except FileNotFoundError:
        return _TOOL_NOT_AVAILABLE


def _get_symbols(nm_args: List[str], lib_file: str) -> str:
    syms = subprocess.run(["nm", *nm_args, *[lib_file]], capture_output=True, check=True).stdout
    return "\n".join(
        [
            line
            for line in syms.decode("utf-8").split("\n")
            if not (" a " in line or "\ta\t" in line)
        ]
    )


def _dsymutil_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    stdout = _run_command(["dsymutil", "-s", lib_file])
    contains_debug_lines = any(bool(re.search(r"\(N_OSO[\t ]+\)", x)) for x in stdout.split("\n"))
    return contains_debug_lines, "dsymutil -s"


def _nm_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    exported_symbols = _get_symbols(nm_args=[], lib_file=lib_file)
    all_symbols = _get_symbols(nm_args=["--debug-syms"], lib_file=lib_file)
    return exported_symbols != all_symbols, "nm --debug-syms"


def _objdump_all_headers_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    stdout = _run_command(["objdump", "--all-headers", lib_file])
    contains_debug_lines = any(
        bool(re.search(r"[\t ]+\.debug_line[\t ]+", x)) for x in stdout.split("\n")
    )
    return contains_debug_lines, "objdump --all-headers"


def _objdump_w_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    stdout = _run_command(["objdump", "-W", lib_file])
    contains_debug_lines = any(
        x.strip().startswith("Contents of the .debug") for x in stdout.split("\n")
    )
    return contains_debug_lines, "objdump -W"


def _objdump_g_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    stdout = _run_command(["objdump", "-g", lib_file])
    contains_debug_lines = any(
        x.strip().startswith("Contents of the .debug") for x in stdout.split("\n")
    )
    return contains_debug_lines, "objdump -g"


def _readelf_reports_debug_symbols(lib_file: str) -> Tuple[bool, str]:
    stdout = _run_command(["readelf", "-S", lib_file])
    contains_debug_lines = any(
        bool(re.search(r"[\t ]+\.debug_[a-z]+[\t ]+", x)) for x in stdout.split("\n")
    )
    return contains_debug_lines, "readelf -S"


def _tar_member_has_debug_symbols(archive_file: str, member: str) -> Tuple[bool, str]:
    with TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            zf.extractall(path=tmp_dir, members=[member])
        full_path = os.path.join(tmp_dir, member)
        check_functions = [
            _dsymutil_reports_debug_symbols,
            _nm_reports_debug_symbols,
            _objdump_all_headers_reports_debug_symbols,
            _objdump_g_reports_debug_symbols,
            _objdump_w_reports_debug_symbols,
            _readelf_reports_debug_symbols,
        ]
        for check_function in check_functions:
            found_debug_symbols, cmd_str = check_function(lib_file=full_path)
            if found_debug_symbols:
                return True, cmd_str
        # at this point, none of the checks found debug symbols
        return False, ""
