# Copyright (c) 2022-2026 the pydistcheck developers. All rights reserved.
"""
functions used to analyze compiled objects

References:
  * https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
"""

import os
import re
import struct
import subprocess

from ._file_utils import (
    _DOS_MZ_MAGIC_FIRST_2_BYTES,
    _ELF_MAGIC,
    _MACH_O_MAGIC_FIRST_4_BYTES,
)

_COMMAND_FAILED = "__command_failed__"
_NO_DEBUG_SYMBOLS = "__no_debug_symbols_found__"
_TOOL_NOT_AVAILABLE = "__tool_not_available__"

# This specific debug symbol is added by Apple's "strip" on
# Mach-O files and can safely be ignored for the purpose of detecting debug symbols. See:
# https://github.com/jameslamb/pydistcheck/issues/235
_MACHO_STRIP_SYMBOL = "radr://5614542"

# --- PE / COFF ---
_PE_SIGNATURE = b"PE\0\0"
_COFF_SECTION_HEADER_SIZE = 40
_COFF_SYMBOL_SIZE = 18
_IMAGE_SYM_CLASS_FILE = 0x67

class _MalformedBinaryError(Exception):
    """
    Placeholder exception for any parsing issues.

    Not intended to be raised directly to users.
    """
    pass


def _read_at(f: BinaryIO, *, offset: int, size: int) -> bytes:
    """
    Read ``size`` bytes in a ``BinaryIO`` object, starting at ``offset``.
    """
    # Offsets and sizes come from the file itself. Check them against the file's size,
    # to prevent a corrupted file from casuing an inappropriate read or
    # huge memory allocation.
    file_size = f.seek(0, os.SEEK_END)
    if offset < 0 or size < 0 or offset + size > file_size:
        raise _MalformedBinaryError
    f.seek(offset)
    return f.read(size)


def _unpack_from(fmt: str, buffer: bytes, offset: int) -> tuple[int, ...]:
    try:
        return struct.unpack_from(fmt, buffer, offset)
    except struct.error as err:
        raise _MalformedBinaryError from err

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
            (["objdump", "--all-headers"],      r"[\t ]+\.debug_line[\t ]+"),
            (["objdump", "-W"],                 r"^Contents of the \.debug"),
            (["objdump", "-g"],                 r"^Contents of the \.debug"),
            (["llvm-objdump", "--all-headers"], r"[\t ]+\.debug_line[\t ]+"),
            (["llvm-objdump", "-W"],            r"^Contents of the \.debug"),
            (["llvm-objdump", "-g"],            r"^Contents of the \.debug"),
            (["readelf", "-S"],                 r"[\t ]+\.debug_[a-z]+[\t ]+"),
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


def _pe_has_debug_symbols(f: BinaryIO) -> tuple[bool, str]:
    """
    Report whether a PE ("Portable Executable") file
    contains debug symbols.

    References:
      * https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
    """

    # PE files are always little-endian
    endian_marker = "<"

    # Every PE file starts w/ a 64-byte MS-DOS header.
    #
    # The last field, starting at offset 0x3C (byte 60), is a 4-byte offset
    # pointing to where the PE header starts.
    pe_signature_offset, *_ = _unpack_from(
        fmt=f"{endian_marker}I",
        buffer=_read_at(f, offset=0x3C, size=4),
        offset=0,
    )
    coff_header = _read_at(f, offset=coff_header_offset, size=24)

    # From the docs:
    #
    #   ... at the file offset specified at offset 0x3c, is a 4-byte signature that identifies the
    #   file as a PE format image file. This signature is "PE\0\0"
    #   (the letters "P" and "E" followed by two null bytes).
    #
    if coff_header[:4] != b"PE\0\0":
        # this must not be a PE file, and therefore not a shared library
        return _NO_DEBUG_SYMBOLS

    # the number of sections is stored as a 16-bit (2-byte) integer, 
    num_sections, * = _unpack_from(
        fmt=f"{endian_marker}H",
        buffer=coff_header,
        offset=6,
    )
    symbol_table_offset, num_symbols = _unpack_from(f"{endian_marker}II", coff_header, 12)
    (optional_header_size,) = _unpack_from(f"{endian_marker}H", coff_header, 20)
    section_headers = _read_at(
        f,
        offset=e_lfanew + 24 + optional_header_size,
        size=num_sections * _COFF_SECTION_HEADER_SIZE,
    )

    string_table = None
    for i in range(num_sections):
        start = i * _COFF_SECTION_HEADER_SIZE
        section_name = section_headers[start : start + 8].rstrip(b"\0")
        # names longer than 8 characters (like MinGW's '.debug_info') are
        # stored in the COFF string table and referenced as '/{offset}'
        if section_name.startswith(b"/") and section_name[1:].isdigit():
            if string_table is None:
                string_table_offset = (
                    symbol_table_offset + num_symbols * _COFF_SYMBOL_SIZE
                )
                (string_table_size,) = _unpack_from(
                    "<I",
                    _read_at(f, offset=string_table_offset, size=4),
                    0,
                )
                string_table = _read_at(
                    f,
                    offset=string_table_offset,
                    size=string_table_size,
                )
            section_name = _c_string_at(string_table, int(section_name[1:]))
        if section_name.startswith(_DEBUG_SECTION_PREFIXES):
            return True, _SECTIONS_CMD

    # COFF symbol tables are deprecated for images, but MinGW still writes them,
    # including '.file' symbols naming the source files
    if symbol_table_offset != 0 and num_symbols > 0:
        symbols = _read_at(
            f,
            offset=symbol_table_offset,
            size=num_symbols * _COFF_SYMBOL_SIZE,
        )
        i = 0
        while i < num_symbols:
            start = i * _COFF_SYMBOL_SIZE
            if symbols[start + 16] == _IMAGE_SYM_CLASS_FILE:
                return True, _SYMBOLS_CMD
            # skip over auxiliary symbol records
            i += 1 + symbols[start + 17]

    return _NO_DEBUG_SYMBOLS

def _file_has_debug_symbols(file_absolute_path: str) -> tuple[bool, str]:

    with open(file_absolute_path, "rb") as f:
        header = f.read(4)
        if header == _ELF_MAGIC:
            return _elf_has_debug_symbols(file_absolute_path)
        if header in _MACH_O_MAGIC_FIRST_4_BYTES:
            return _macho_has_debug_symbols(file_absolute_path)
        if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
            return _pe_has_debug_symbols(file_absolute_path)

        # any file not in a recognizable format should be marked as not having debug symbols
        return False, ""
