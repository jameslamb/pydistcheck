# Copyright (c) 2022-2026 the pydistcheck developers. All rights reserved.
"""
functions used to analyze compiled objects
"""

import re
import subprocess

from ._file_utils import (
    _DOS_MZ_MAGIC_FIRST_2_BYTES,
    _ELF_MAGIC_FIRST_4_BYTES,
    _MACH_O_MAGIC_FIRST_4_BYTES,
)

_COMMAND_FAILED = "__command_failed__"
_NO_DEBUG_SYMBOLS = "__no_debug_symbols_found__"
_TOOL_NOT_AVAILABLE = "__tool_not_available__"

# This specific debug symbol is added by Apple's "strip" on
# Mach-O files and can safely be ignored for the purpose of detecting debug symbols. See:
# https://github.com/jameslamb/pydistcheck/issues/235
_MACHO_STRIP_SYMBOL = "radr://5614542"


def _run_command(args: list[str]) -> str:
    try:
        stdout = subprocess.run(args, capture_output=True, check=True).stdout
        # Use latin1 encoding, which can handle any byte value without data loss.
        # See https://github.com/jameslamb/pydistcheck/issues/206 for rationale.
        return stdout.decode("latin1")
    except subprocess.CalledProcessError:
        return _COMMAND_FAILED
    except FileNotFoundError:
        return _TOOL_NOT_AVAILABLE


def _look_for_debug_symbols(
    lib_file: str,
    commands_to_patterns: list[tuple[list[str], str]],
) -> tuple[bool, str]:
    for cmd_args, pattern in commands_to_patterns:
        stdout = _run_command(args=[*cmd_args, lib_file])
        contains_debug_symbols = any(
            bool(re.search(pattern, x)) for x in stdout.split("\n")
        )
        if contains_debug_symbols:
            return True, " ".join(cmd_args)
    # if you get here, no debug symbols were found by any tools
    return False, _NO_DEBUG_SYMBOLS


def _get_symbols(cmd_args: list[str], lib_file: str) -> str:
    syms = _run_command(args=[*cmd_args, lib_file])
    return "\n".join(
        [line for line in syms.split("\n") if line and _MACHO_STRIP_SYMBOL not in line],
    )


def _nm_reports_debug_symbols(tool_name: str, lib_file: str) -> tuple[bool, str]:
    exported_symbols = _get_symbols(cmd_args=[tool_name], lib_file=lib_file)
    all_symbols = _get_symbols(cmd_args=[tool_name, "-a"], lib_file=lib_file)
    return exported_symbols != all_symbols, f"{tool_name} -a"


def _elf_has_debug_symbols(f: str) -> tuple[bool, str]:
    """
    Report whether an ELF ("Executable and Linkable Format") file
    contains debug symbols.
    """
    # test with tools that produce debug symbols that can be matched with a regex
    # fmt: off
    has_debug_symbols, cmd_str = _look_for_debug_symbols(
        lib_file=f,
        commands_to_patterns=[
            (["readelf", "-S"],                 r"[\t ]+\.debug_[a-z]+[\t ]+"),
            (["objdump", "--all-headers"],      r"[\t ]+\.debug_line[\t ]+"),
            (["objdump", "-W"],                 r"^Contents of the \.debug"),
            (["objdump", "-g"],                 r"^Contents of the \.debug"),
            (["llvm-objdump", "--all-headers"], r"[\t ]+\.debug_line[\t ]+"),
            (["llvm-objdump", "-W"],            r"^Contents of the \.debug"),
            (["llvm-objdump", "-g"],            r"^Contents of the \.debug"),
        ],
    )
    # fmt: on
    if has_debug_symbols:
        return True, cmd_str

    # "nm"'s test is like "check if the output is different when a flag is supplied",
    # instead of "test if this tool produces output matching this regex",
    # so it runs separately here
    for nm_tool in ["nm", "llvm-nm"]:
        has_debug_symbols, cmd_str = _nm_reports_debug_symbols(
            tool_name=nm_tool,
            lib_file=f,
        )
        if has_debug_symbols:  # pragma: no cover
            return True, cmd_str

    return False, cmd_str


def _macho_has_debug_symbols(f: str) -> tuple[bool, str]:
    """
    Report whether a Mach-O ("Mach object") file
    contains debug symbols.
    """
    # test with tools that produce debug symbols that can be matched with a regex
    # fmt:off
    has_debug_symbols, cmd_str = _look_for_debug_symbols(
        lib_file=f,
        commands_to_patterns=[
            (["dsymutil", "-s"],                           r"\(N_OSO[\t ]+\)"),
            (["objdump", "--macho", "--all-headers"],      r"[\t ]+\.debug_line[\t ]+"),
            (["objdump", "--macho", "-W"],                 r"^Contents of the \.debug"),
            (["objdump", "--macho", "-g"],                 r"^Contents of the \.debug"),
            (["llvm-objdump", "--macho", "--all-headers"], r"[\t ]+\.debug_line[\t ]+"),
            (["llvm-objdump", "--macho", "-W"],            r"^Contents of the \.debug"),
            (["llvm-objdump", "--macho", "-g"],            r"^Contents of the \.debug"),
        ],
    )
    # fmt:on
    if has_debug_symbols:
        return True, cmd_str

    # "nm"'s test is like "check if the output is different when a flag is supplied",
    # instead of "test if this tool produces output matching this regex",
    # so it runs separately here
    for nm_tool in ["nm", "llvm-nm"]:
        has_debug_symbols, cmd_str = _nm_reports_debug_symbols(
            tool_name=nm_tool,
            lib_file=f,
        )
        if has_debug_symbols:  # pragma: no cover
            return True, cmd_str

    return False, cmd_str


def _pe_has_debug_symbols(f: str) -> tuple[bool, str]:
    """
    Report whether a PE ("Portable Executable") file
    contains debug symbols.
    """
    # test with tools that produce debug symbols that can be matched with a regex
    # fmt: off
    has_debug_symbols, cmd_str = _look_for_debug_symbols(
        lib_file=f,
        commands_to_patterns=[
            (["objdump", "--all-headers"],      r"[\t ]+\.debug_line[\t ]+"),
            (["objdump", "-W"],                 r"^Contents of the \.debug"),
            (["objdump", "-g"],                 r"^Contents of the \.debug"),
            (["llvm-objdump", "--all-headers"], r"[\t ]+\.debug_line[\t ]+"),
            (["llvm-objdump", "-W"],            r"^Contents of the \.debug"),
            (["llvm-objdump", "-g"],            r"^Contents of the \.debug"),
        ],
    )
    # fmt: on
    if has_debug_symbols:
        return True, cmd_str

    # "nm"'s test is like "check if the output is different when a flag is supplied",
    # instead of "test if this tool produces output matching this regex",
    # so it runs separately here
    for nm_tool in ["nm", "llvm-nm"]:
        has_debug_symbols, cmd_str = _nm_reports_debug_symbols(
            tool_name=nm_tool,
            lib_file=f,
        )
        if has_debug_symbols:  # pragma: no cover
            return True, cmd_str

    return False, cmd_str


def _file_has_debug_symbols(file_absolute_path: str) -> tuple[bool, str]:

    with open(file_absolute_path, "rb") as f:
        header = f.read(4)
        if header in _ELF_MAGIC_FIRST_4_BYTES:
            return _elf_has_debug_symbols(file_absolute_path)
        if header in _MACH_O_MAGIC_FIRST_4_BYTES:
            return _macho_has_debug_symbols(file_absolute_path)
        if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
            return _pe_has_debug_symbols(file_absolute_path)

        # any file not in a recognizable format should be marked as not having debug symbols
        return False, ""
