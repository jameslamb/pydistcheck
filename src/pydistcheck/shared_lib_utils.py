"""
functions used to analyze compiled objects
"""

import os
import subprocess
import zipfile
from tempfile import TemporaryDirectory
from typing import List

# https://stackoverflow.com/questions/35865099/python-extracting-specific-files-with-pattern-from-tar-gz-without-extracting-th
# https://linux.die.net/man/1/nm


def _get_symbols(nm_args: List[str], lib_file: str) -> str:
    syms = subprocess.run(["nm", *nm_args, *[lib_file]], capture_output=True, check=True).stdout
    return "\n".join(
        [
            line
            for line in syms.decode("utf-8").split("\n")
            if not (" a " in line or "\ta\t" in line)
        ]
    )


def _tar_member_has_debug_symbols(archive_file: str, member: str) -> bool:
    with TemporaryDirectory() as tmp_dir:
        with zipfile.ZipFile(archive_file, mode="r") as zf:
            zf.extractall(path=tmp_dir, members=[member])
            full_path = os.path.join(tmp_dir, member)
            exported_symbols = _get_symbols(nm_args=[], lib_file=full_path)
            all_symbols = _get_symbols(nm_args=["--debug-syms"], lib_file=full_path)
    return exported_symbols != all_symbols
