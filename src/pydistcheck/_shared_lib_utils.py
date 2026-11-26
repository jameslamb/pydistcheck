# Copyright (c) 2022-2026 the pydistcheck developers. All rights reserved.
"""
functions used to analyze compiled objects
"""

import os
import re
import struct
import subprocess
from typing import BinaryIO, NamedTuple

from ._file_utils import (
    _DOS_MZ_MAGIC_FIRST_2_BYTES,
    _ELF_MAGIC,
    _MACH_O_MAGIC_FIRST_4_BYTES,
)

# commands suggested to users who want to see the debug information for themselves
_SECTIONS_CMD = "objdump -h"
_SYMBOLS_CMD = "nm -a"

_COMMAND_FAILED = "__command_failed__"
_NO_DEBUG_SYMBOLS: tuple[bool, str] = (False, "")
_TOOL_NOT_AVAILABLE = "__tool_not_available__"

# section names produced for DWARF debug information
# ('.zdebug_' is the older compressed-DWARF convention)
_DEBUG_SECTION_PREFIXES = (b".debug_", b".zdebug_")

# --- ELF ---
_ELFCLASS32 = 1
_ELFCLASS64 = 2
_ELFDATA2LSB = 1
_ELFDATA2MSB = 2
_SHN_XINDEX = 0xFFFF
_SHT_SYMTAB = 2
_STT_SECTION = 3
_STT_FILE = 4

# Lookup table for bytes.translate(): 1 where the symbol type (low 4 bits of 'st_info')
# is one of the "debugger-only" types that 'nm' hides unless passed '-a'.
_ELF_DEBUGGER_ONLY_SYMBOL_TYPES = bytes(
    1 if (i & 0xF) in (_STT_SECTION, _STT_FILE) else 0 for i in range(256)
)

# This specific debug symbol is added by Apple's "strip" on
# Mach-O files and can safely be ignored for the purpose of detecting debug symbols. See:
# https://github.com/jameslamb/pydistcheck/issues/235
_MACHO_STRIP_SYMBOL = "radr://5614542"


class _MalformedBinaryError(Exception):
    """
    Placeholder exception for any parsing issues.

    Not intended to be raised directly to users.
    """


def _read_at(f: BinaryIO, *, offset: int, size: int) -> bytes:
    """
    Read ``size`` bytes in a ``BinaryIO`` object, starting at ``offset``.
    """
    # Offsets and sizes come from the file itself. Check them against the file's size,
    # to prevent a corrupted file from causing an inappropriate read or
    # huge memory allocation.
    file_size = f.seek(0, os.SEEK_END)
    if offset < 0 or size < 0 or offset + size > file_size:
        raise _MalformedBinaryError  # pragma: no cover
    f.seek(offset)
    return f.read(size)


def _unpack_from(fmt: str, buffer: bytes, offset: int) -> tuple[int, ...]:
    try:
        return struct.unpack_from(fmt, buffer, offset)
    except struct.error as err:  # pragma: no cover
        raise _MalformedBinaryError from err


def _c_string_at(buffer: bytes, offset: int) -> bytes:
    if not 0 <= offset < len(buffer):
        raise _MalformedBinaryError  # pragma: no cover
    end = buffer.find(b"\0", offset)
    if end == -1:
        return buffer[offset:]  # pragma: no cover
    return buffer[offset:end]


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
    return False, ""


def _get_symbols(cmd_args: list[str], lib_file: str) -> str:
    syms = _run_command(args=[*cmd_args, lib_file])
    return "\n".join(
        [line for line in syms.split("\n") if line and _MACHO_STRIP_SYMBOL not in line],
    )


def _nm_reports_debug_symbols(tool_name: str, lib_file: str) -> tuple[bool, str]:
    exported_symbols = _get_symbols(cmd_args=[tool_name], lib_file=lib_file)
    all_symbols = _get_symbols(cmd_args=[tool_name, "-a"], lib_file=lib_file)
    return exported_symbols != all_symbols, f"{tool_name} -a"


class _ElfSectionHeader(NamedTuple):
    sh_name: int
    sh_type: int
    sh_flags: int
    sh_addr: int
    sh_offset: int
    sh_size: int
    sh_link: int
    sh_info: int
    sh_addralign: int
    sh_entsize: int


class _ElfLayout(NamedTuple):
    section_headers: list[_ElfSectionHeader]
    # contents of the section that holds section names ('.shstrtab')
    section_names: bytes
    # byte offset of 'st_info' within each symbol table entry
    st_info_offset: int


def _read_elf_layout(f: BinaryIO) -> _ElfLayout:
    ident = _read_at(f, offset=0, size=16)
    ei_class, ei_data = ident[4], ident[5]
    if ei_data == _ELFDATA2LSB:
        endian = "<"
    elif ei_data == _ELFDATA2MSB:
        endian = ">"
    else:
        raise _MalformedBinaryError

    if ei_class == _ELFCLASS64:
        header = _read_at(f, offset=0, size=64)
        (shoff,) = _unpack_from(endian + "Q", header, 0x28)
        shentsize, shnum, shstrndx = _unpack_from(endian + "HHH", header, 0x3A)
        shdr_fmt = endian + "IIQQQQIIQQ"
        st_info_offset = 4
    elif ei_class == _ELFCLASS32:
        header = _read_at(f, offset=0, size=52)
        (shoff,) = _unpack_from(endian + "I", header, 0x20)
        shentsize, shnum, shstrndx = _unpack_from(endian + "HHH", header, 0x2E)
        shdr_fmt = endian + "IIIIIIIIII"
        st_info_offset = 12
    else:
        raise _MalformedBinaryError

    # no section header table (e.g. fully-stripped with 'sstrip')
    if shoff == 0:
        return _ElfLayout(
            section_headers=[],
            section_names=b"",
            st_info_offset=st_info_offset,
        )

    if shentsize < struct.calcsize(shdr_fmt):
        raise _MalformedBinaryError

    # for files with >= 0xff00 sections, the real values live in section header 0
    first = _ElfSectionHeader(
        *_unpack_from(shdr_fmt, _read_at(f, offset=shoff, size=shentsize), 0),
    )
    if shnum == 0:
        shnum = first.sh_size
    if shstrndx == _SHN_XINDEX:
        shstrndx = first.sh_link
    if shstrndx >= shnum:
        raise _MalformedBinaryError

    raw = _read_at(f, offset=shoff, size=shentsize * shnum)
    section_headers = [
        _ElfSectionHeader(*_unpack_from(shdr_fmt, raw, i * shentsize))
        for i in range(shnum)
    ]
    shstrtab = section_headers[shstrndx]
    return _ElfLayout(
        section_headers=section_headers,
        section_names=_read_at(f, offset=shstrtab.sh_offset, size=shstrtab.sh_size),
        st_info_offset=st_info_offset,
    )


def _elf_has_debug_symbols(f: BinaryIO) -> tuple[bool, str]:
    """
    Report whether an ELF ("Executable and Linkable Format") file
    contains debug symbols.
    """
    section_headers, section_names, st_info_offset = _read_elf_layout(f)
    symtabs = []
    for shdr in section_headers:
        if _c_string_at(section_names, shdr.sh_name).startswith(
            _DEBUG_SECTION_PREFIXES,
        ):
            return True, _SECTIONS_CMD
        if shdr.sh_type == _SHT_SYMTAB:
            symtabs.append(shdr)

    for symtab in symtabs:
        entsize = symtab.sh_entsize
        if entsize <= st_info_offset:
            continue
        data = _read_at(f, offset=symtab.sh_offset, size=symtab.sh_size)
        # every 'st_info' byte, skipping the reserved null symbol at index 0
        num_symbols = len(data) // entsize
        st_info = data[entsize + st_info_offset : num_symbols * entsize : entsize]
        if b"\x01" in st_info.translate(_ELF_DEBUGGER_ONLY_SYMBOL_TYPES):
            return True, _SYMBOLS_CMD

    return _NO_DEBUG_SYMBOLS


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
    Report whether a PE ("Portable Executable") file contains debug symbols.

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
    pe_signature = _read_at(f, offset=pe_signature_offset, size=4)

    # From the docs:
    #
    #   ... at the file offset specified at offset 0x3c, is a 4-byte signature that identifies the
    #   file as a PE format image file. This signature is "PE\0\0"
    #   (the letters "P" and "E" followed by two null bytes).
    #
    if pe_signature != b"PE\0\0":
        # this must not be a PE file, and therefore not a shared library
        return _NO_DEBUG_SYMBOLS  # pragma: no cover

    # COFF header begins 4 bytes after the PE signature.
    coff_header_offset = pe_signature_offset + 4

    # See https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#coff-file-header-object-and-image for
    # the structure of the COFF header.
    #
    # Paraphrasing:
    #
    #   * bytes  0-1: (ignored here)
    #   * bytes  2-3: total number of sections in the section table
    #   * bytes  4-7: (ignored here)
    #   * bytes  8-11: file offset of the COFF symbol table (or 0 if it isn't present)
    #   * bytes 12-15: total number of symbols in the symbol table
    #   * bytes 16-17: size of the "optional" header
    #   * bytes 18-19: (ignored here)
    #
    coff_header_format = f"{endian_marker}HHIIIHH"
    coff_header = _read_at(
        f,
        offset=coff_header_offset,
        size=struct.calcsize(coff_header_format),
    )
    # fmt: off
    _, num_sections, _, symbol_table_offset, num_symbols, optional_header_size, _, = _unpack_from(
        fmt=coff_header_format,
        buffer=coff_header,
        offset=0,
    )
    # fmt: on

    # Section table immediately follows the "optional header".
    #
    coff_section_header_size = 40
    section_headers = _read_at(
        f,
        offset=coff_header_offset + len(coff_header) + optional_header_size,
        size=num_sections * coff_section_header_size,
    )

    # The string table immediately follows the symbol table.
    #
    # Each entry in the symbol table is 18 bytes.
    #
    coff_symbol_size = 18
    string_table_offset = symbol_table_offset + num_symbols * coff_symbol_size

    # Look for sections with names that look like they contain debug symbols.
    #
    # Again paraphrasing the docs, each section header (section table entry) has the following format,
    # for a total of 40 bytes per entry.
    #
    #   * bytes 0-8: section name
    #   * bytes 9-39: (ignored here)
    #

    # Long section names (like '.debug_info') might not be in the 'Name' attribute in the section
    # header, but might not to be looked up in the file's string table.
    #
    #   > For [names longer than 8 characters], [the "Name" field] contains a slash (/) that is followed
    #     by an ASCII representation of a decimal number that is an offset into the string table.
    #
    # That table could be large, so instead of eagerly reading it here, only read it on demand if needed.
    string_table = None
    for i in range(num_sections):
        start = i * coff_section_header_size
        section_name = section_headers[start : start + 8].rstrip(b"\0")

        # if the string table needs to be read and isn't yet, read it
        if section_name.startswith(b"/") and section_name[1:].isdigit():
            if string_table is None:
                string_table_size, *_ = _unpack_from(
                    fmt=f"{endian_marker}I",
                    buffer=_read_at(f, offset=string_table_offset, size=4),
                    offset=0,
                )
                string_table = _read_at(
                    f,
                    offset=string_table_offset,
                    size=string_table_size,
                )

            # read into the string table
            section_name = _c_string_at(
                buffer=string_table,
                offset=int(section_name[1:]),
            )
        if section_name.startswith(_DEBUG_SECTION_PREFIXES):
            return True, _SECTIONS_CMD

    # COFF symbol tables are deprecated for images, but MinGW still writes them,
    # including '.file' symbols naming the source files.
    if symbol_table_offset != 0 and num_symbols > 0:
        # read the entire table ... it should typically be small in memory, and 1 big read is
        # much faster than potentially thousands of tiny reads.
        symbols = _read_at(
            f,
            offset=symbol_table_offset,
            size=num_symbols * coff_symbol_size,
        )
        i = 0
        while i < num_symbols:
            # symbols are 18-byte records structured like this (paraphrasing):
            #
            #  * bytes 0-8: name (ignored here)
            #  * bytes 9-16: (ignored here)
            #  * byte 17: storage class
            #  * byte 18: number of auxiliary symbols that follows it
            #
            # ref: https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#coff-symbol-table
            #
            start = i * coff_symbol_size

            # 103 is the storage class for .file symbols, which record the path
            # to the file the symbol came from.
            #
            # From the docs
            #
            #   > IMAGE_SYM_CLASS_FILE (103)
            #   >
            #   > A value that Microsoft tools, as well as traditional COFF format,
            #   > use for the source-file symbol record. The symbol is followed by auxiliary
            #   > records that name the file.
            #
            # These are stripped in release builds, so should be treated as "debug" symbols too.
            if symbols[start + 16] == 103:
                return True, _SYMBOLS_CMD

            # The 18th byte holds the number of "auxiliary" records... those should all
            # be skipped for this check. This is only interested in "real" symbols and whether
            # they look like .file symbols.
            i += 1 + symbols[start + 17]

    return _NO_DEBUG_SYMBOLS


def _file_has_debug_symbols(file_absolute_path: str) -> tuple[bool, str]:

    with open(file_absolute_path, "rb") as f:
        header = f.read(4)
        try:
            if header == _ELF_MAGIC:
                return _elf_has_debug_symbols(f)
            if header in _MACH_O_MAGIC_FIRST_4_BYTES:
                return _macho_has_debug_symbols(file_absolute_path)
            if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
                return _pe_has_debug_symbols(f)
        except _MalformedBinaryError:  # pragma: no cover
            # files that cannot be parsed are treated as not having debug symbols
            return _NO_DEBUG_SYMBOLS

        # any file not in a recognizable format should be marked as not having debug symbols
        return _NO_DEBUG_SYMBOLS
