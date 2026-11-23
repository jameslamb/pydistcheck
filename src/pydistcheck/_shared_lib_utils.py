# Copyright (c) 2022-2026 the pydistcheck developers. All rights reserved.
"""
functions used to analyze compiled objects

Debug symbols are detected by reading ELF, Mach-O, and PE headers directly
(with only the standard library), instead of shelling out to tools like
'objdump', 'nm', 'readelf', and 'dsymutil'.

References:
  * https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.sheader.html
  * https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.symtab.html
  * https://github.com/apple-oss-distributions/xnu/blob/5c2921b07a2480ab43ec66f5b9e41cb872bc554f/EXTERNAL_HEADERS/mach-o/loader.h
  * https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/fat.h
  * https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/stab.h
  * https://learn.microsoft.com/en-us/windows/win32/debug/pe-format

"""

import os
import struct
from typing import BinaryIO, NamedTuple

from ._file_utils import (
    _DOS_MZ_MAGIC_FIRST_2_BYTES,
    _ELF_MAGIC_FIRST_4_BYTES,
    _MACH_O_MAGIC_FIRST_4_BYTES,
)

# commands suggested to users who want to see the debug information for themselves
_SECTIONS_CMD = "objdump -h"
_SYMBOLS_CMD = "nm -a"

_NO_DEBUG_SYMBOLS: tuple[bool, str] = (False, "")

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

# --- Mach-O ---
_MH_MAGIC = 0xFEEDFACE
_MH_MAGIC_64 = 0xFEEDFACF
_FAT_MAGIC = 0xCAFEBABE
_FAT_MAGIC_64 = 0xCAFEBABF
_LC_SEGMENT = 0x1
_LC_SYMTAB = 0x2
_LC_SEGMENT_64 = 0x19
_N_STAB = 0xE0
_DWARF_SEGMENT_NAME = b"__DWARF"

# Lookup table for bytes.translate(): 1 where 'n_type' marks a symbolic debugging
# ("stab") entry, which 'nm' hides unless passed '-a'.
_MACHO_STAB_TYPES = bytes(1 if i & _N_STAB else 0 for i in range(256))

# This specific debug symbol is added by Apple's "strip" on
# Mach-O files and can safely be ignored for the purpose of detecting debug symbols. See:
# https://github.com/jameslamb/pydistcheck/issues/235
_MACHO_STRIP_SYMBOL = b"radr://5614542"

# --- PE / COFF ---
_PE_SIGNATURE = b"PE\0\0"
_COFF_SECTION_HEADER_SIZE = 40
_COFF_SYMBOL_SIZE = 18
_IMAGE_SYM_CLASS_FILE = 0x67


class _MalformedBinaryError(Exception):
    pass


def _read_at(f: BinaryIO, *, offset: int, size: int) -> bytes:
    # Offsets and sizes come from the file itself, so check them against the file's
    # size before reading. Otherwise, a corrupt value could lead to an attempt to
    # allocate a huge buffer (MemoryError or OverflowError).
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


def _c_string_at(buffer: bytes, offset: int) -> bytes:
    if not 0 <= offset < len(buffer):
        raise _MalformedBinaryError
    end = buffer.find(b"\0", offset)
    return buffer[offset:] if end == -1 else buffer[offset:end]


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


def _macho_segment_is_dwarf(
    load_commands: bytes,
    *,
    offset: int,
    endian: str,
    is_64: bool,
) -> bool:
    if load_commands[offset + 8 : offset + 24].rstrip(b"\0") == _DWARF_SEGMENT_NAME:
        return True
    # in object files, all sections live in a single unnamed segment,
    # so also check the segment name recorded on each section
    if is_64:
        (nsects,) = _unpack_from(endian + "I", load_commands, offset + 64)
        sections_start, section_size = offset + 72, 80
    else:
        (nsects,) = _unpack_from(endian + "I", load_commands, offset + 48)
        sections_start, section_size = offset + 56, 68
    for i in range(nsects):
        segname_start = sections_start + i * section_size + 16
        segname = load_commands[segname_start : segname_start + 16]
        if len(segname) != 16:
            raise _MalformedBinaryError
        if segname.rstrip(b"\0") == _DWARF_SEGMENT_NAME:
            return True
    return False


def _thin_macho_has_debug_symbols(f: BinaryIO, *, base: int) -> tuple[bool, str]:  # noqa: C901
    header = _read_at(f, offset=base, size=28)
    (magic,) = _unpack_from("<I", header, 0)
    if magic in (_MH_MAGIC, _MH_MAGIC_64):
        endian = "<"
    else:
        endian = ">"
        (magic,) = _unpack_from(">I", header, 0)
        if magic not in (_MH_MAGIC, _MH_MAGIC_64):
            raise _MalformedBinaryError
    is_64 = magic == _MH_MAGIC_64
    ncmds, sizeofcmds = _unpack_from(endian + "II", header, 16)
    header_size = 32 if is_64 else 28
    load_commands = _read_at(f, offset=base + header_size, size=sizeofcmds)

    symtab = None
    offset = 0
    for _ in range(ncmds):
        cmd, cmdsize = _unpack_from(endian + "II", load_commands, offset)
        if cmdsize < 8 or offset + cmdsize > len(load_commands):
            raise _MalformedBinaryError
        if cmd in (_LC_SEGMENT, _LC_SEGMENT_64) and _macho_segment_is_dwarf(
            load_commands,
            offset=offset,
            endian=endian,
            is_64=cmd == _LC_SEGMENT_64,
        ):
            return True, _SECTIONS_CMD
        if cmd == _LC_SYMTAB:
            symtab = _unpack_from(endian + "IIII", load_commands, offset + 8)
        offset += cmdsize

    if symtab is None:
        return _NO_DEBUG_SYMBOLS

    symoff, nsyms, stroff, strsize = symtab
    nlist_size = 16 if is_64 else 12
    symbols = _read_at(f, offset=base + symoff, size=nsyms * nlist_size)
    n_types = symbols[4::nlist_size]
    is_stab = n_types.translate(_MACHO_STAB_TYPES)
    if b"\x01" not in is_stab:
        return _NO_DEBUG_SYMBOLS

    strings = _read_at(f, offset=base + stroff, size=strsize)
    i = is_stab.find(b"\x01")
    while i != -1:
        (n_strx,) = _unpack_from(endian + "I", symbols, i * nlist_size)
        if _c_string_at(strings, n_strx) != _MACHO_STRIP_SYMBOL:
            return True, _SYMBOLS_CMD
        i = is_stab.find(b"\x01", i + 1)
    return _NO_DEBUG_SYMBOLS


def _macho_has_debug_symbols(f: BinaryIO) -> tuple[bool, str]:
    """
    Report whether a Mach-O ("Mach object") file
    contains debug symbols.
    """
    header = _read_at(f, offset=0, size=8)
    magic, nfat_arch = _unpack_from(">II", header, 0)
    if magic not in (_FAT_MAGIC, _FAT_MAGIC_64):
        return _thin_macho_has_debug_symbols(f, base=0)

    if magic == _FAT_MAGIC_64:
        fat_arch_fmt, fat_arch_size = ">iiQ", 32
    else:
        fat_arch_fmt, fat_arch_size = ">iiI", 20
    fat_arches = _read_at(f, offset=8, size=nfat_arch * fat_arch_size)
    for i in range(nfat_arch):
        _cputype, _cpusubtype, offset = _unpack_from(
            fat_arch_fmt,
            fat_arches,
            i * fat_arch_size,
        )
        result = _thin_macho_has_debug_symbols(f, base=offset)
        if result[0]:
            return result
    return _NO_DEBUG_SYMBOLS


def _pe_has_debug_symbols(f: BinaryIO) -> tuple[bool, str]:
    """
    Report whether a PE ("Portable Executable") file
    contains debug symbols.
    """
    (e_lfanew,) = _unpack_from("<I", _read_at(f, offset=0x3C, size=4), 0)
    coff_header = _read_at(f, offset=e_lfanew, size=24)
    # 'MZ' but not PE (e.g. a DOS executable)
    if coff_header[:4] != _PE_SIGNATURE:
        return _NO_DEBUG_SYMBOLS
    (num_sections,) = _unpack_from("<H", coff_header, 6)
    symbol_table_offset, num_symbols = _unpack_from("<II", coff_header, 12)
    (optional_header_size,) = _unpack_from("<H", coff_header, 20)
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
        try:
            if header in _ELF_MAGIC_FIRST_4_BYTES:
                return _elf_has_debug_symbols(f)
            if header in _MACH_O_MAGIC_FIRST_4_BYTES:
                return _macho_has_debug_symbols(f)
            if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
                return _pe_has_debug_symbols(f)
        except _MalformedBinaryError:
            # files that cannot be parsed are treated as not having debug symbols
            return _NO_DEBUG_SYMBOLS

        # any file not in a recognizable format should be marked as not having debug symbols
        return _NO_DEBUG_SYMBOLS
