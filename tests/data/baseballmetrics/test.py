"""
functions used to analyze compiled objects
"""

import os
import subprocess
import zipfile
import re
from tempfile import TemporaryDirectory
from typing import List
import sys

LIB_FILE = sys.argv[1]

# https://stackoverflow.com/questions/35865099/python-extracting-specific-files-with-pattern-from-tar-gz-without-extracting-th
# https://linux.die.net/man/1/nm


def _run_command(args: List[str]) -> str:
    stdout = subprocess.run(args, capture_output=True, check=True).stdout
    return stdout.decode("utf-8")


def _get_symbols(nm_args: List[str], lib_file: str) -> str:
    syms = subprocess.run(["nm", *nm_args, *[lib_file]], capture_output=True, check=True).stdout
    return "\n".join(
        [
            line
            for line in syms.decode("utf-8").split("\n")
            if not (" a " in line or "\ta\t" in line)
        ]
    )


def _nm_reports_debug_symbols(lib_file: str):
    exported_symbols = _get_symbols(nm_args=[], lib_file=lib_file)
    all_symbols = _get_symbols(nm_args=["--debug-syms"], lib_file=lib_file)
    return exported_symbols != all_symbols


def _objdump_all_headers_reports_debug_symbols(lib_file: str) -> bool:
    #stdout = subprocess.run(["objdump", "--all-headers", lib_file], capture_output=True, check=True).stdout
    stdout = _run_command(["objdump", "--all-headers", lib_file])
    contains_debug_lines = any(
        bool(re.search(r"[\t ]+\.debug_line[\t ]+", x))
        for x in stdout.split("\n")
    )
    return contains_debug_lines


def _objdump_w_reports_debug_symbols(lib_file: str) -> bool:
    stdout = _run_command(["objdump", "-W", lib_file])
    #stdout = subprocess.run(["objdump", "-W", lib_file], capture_output=True, check=True).stdout
    contains_debug_lines = any(
        x.strip().startswith("Contents of the .debug")
        for x in stdout.split("\n")
    )
    return contains_debug_lines


def _objdump_g_reports_debug_symbols(lib_file: str) -> bool:
    #stdout = subprocess.run(["objdump", "-g", lib_file], capture_output=True, check=True).stdout
    stdout = _run_command(["objdump", "-g", lib_file])
    contains_debug_lines = any(
        x.strip().startswith("Contents of the .debug")
        for x in stdout.split("\n")
    )
    return contains_debug_lines


def _readelf_reports_debug_symbols(lib_file: str) -> bool:
    #stdout = subprocess.run(["readelf", "--debug-dump", lib_file], capture_output=True, check=True).stdout
    stdout = _run_command(["readelf", "--debug-dump", lib_file])
    contains_debug_lines = any(
        x.strip().startswith("Contents of the .debug")
        for x in stdout.split("\n")
    )
    return contains_debug_lines


def _tar_member_has_debug_symbols(archive_file: str, member: str) -> bool:
    with TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            zf.extractall(path=tmp_dir, members=[member])
            full_path = os.path.join(tmp_dir, member)
            exported_symbols = _get_symbols(nm_args=[], lib_file=full_path)
            all_symbols = _get_symbols(nm_args=["--debug-syms"], lib_file=full_path)
    return exported_symbols != all_symbols



def _has_debug_symbols(lib_file: str) -> bool:
    


if __name__ == "__main__":

    res = _nm_reports_debug_symbols(LIB_FILE)
    print(f"nm: {res}")

    res = _objdump_all_headers_reports_debug_symbols(LIB_FILE)
    print(f"objdump --all-headers: {res}")

    res = _objdump_g_reports_debug_symbols(LIB_FILE)
    print(f"objdump -g: {res}")

    res = _objdump_w_reports_debug_symbols(LIB_FILE)
    print(f"objdump -W: {res}")

    res = _readelf_reports_debug_symbols(LIB_FILE)
    print(f"readelf --debug-dump: {res}")
