import struct
from typing import Optional

import pytest

from pydistcheck._shared_lib_utils import (
    _MACHO_STRIP_SYMBOL,
    _file_has_debug_symbols,
)

_NO_DEBUG_SYMBOLS = (False, "")
_FOUND_DEBUG_SECTIONS = (True, "objdump -h")
_FOUND_DEBUG_SYMBOLS = (True, "nm -a")

# ELF symbol types
_STT_FUNC = 2
_STT_FILE = 4


def _string_table(names: list[bytes]) -> tuple[bytes, list[int]]:
    """Returns (table, offsets) for a NUL-separated string table starting with b'\\0'."""
    table = b"\0"
    offsets = []
    for name in names:
        offsets.append(len(table))
        table += name + b"\0"
    return table, offsets


def _make_elf(
    *,
    is_64: bool = True,
    endian: str = "<",
    section_names: tuple[bytes, ...] = (b".text",),
    symbol_types: Optional[list[int]] = None,
    extended_numbering: bool = False,
) -> bytes:
    shdr_fmt = endian + ("IIQQQQIIQQ" if is_64 else "IIIIIIIIII")
    shdr_size = struct.calcsize(shdr_fmt)
    header_size = 64 if is_64 else 52
    sym_size = 24 if is_64 else 16

    all_names = [b".shstrtab", *section_names]
    if symbol_types is not None:
        all_names.append(b".symtab")
    shstrtab, name_offsets = _string_table(all_names)

    symtab = b""
    if symbol_types is not None:
        # reserved null symbol, then one symbol per requested type
        symtab = b"\0" * sym_size
        for symbol_type in symbol_types:
            if is_64:
                symtab += struct.pack(endian + "IBBHQQ", 0, symbol_type, 0, 0, 0, 0)
            else:
                symtab += struct.pack(endian + "IIIBBH", 0, 0, 0, symbol_type, 0, 0)

    shstrtab_offset = header_size
    symtab_offset = shstrtab_offset + len(shstrtab)
    shoff = symtab_offset + len(symtab)

    shnum = 1 + len(all_names)
    shdrs = [
        # section 0, which holds the real counts when using extended numbering
        struct.pack(
            shdr_fmt,
            0,
            0,
            0,
            0,
            0,
            shnum if extended_numbering else 0,
            1 if extended_numbering else 0,
            0,
            0,
            0,
        ),
        # .shstrtab (SHT_STRTAB)
        struct.pack(
            shdr_fmt,
            name_offsets[0],
            3,
            0,
            0,
            shstrtab_offset,
            len(shstrtab),
            0,
            0,
            1,
            0,
        ),
    ]
    # other sections have no contents (SHT_PROGBITS)
    shdrs.extend(
        struct.pack(shdr_fmt, name_offsets[i], 1, 0, 0, 0, 0, 0, 0, 1, 0)
        for i in range(1, len(section_names) + 1)
    )
    if symbol_types is not None:
        # .symtab (SHT_SYMTAB)
        shdrs.append(
            struct.pack(
                shdr_fmt,
                name_offsets[-1],
                2,
                0,
                0,
                symtab_offset,
                len(symtab),
                0,
                0,
                8,
                sym_size,
            )
        )

    ident = (
        b"\x7fELF"
        + bytes([2 if is_64 else 1, 1 if endian == "<" else 2, 1])
        + b"\0" * 9
    )
    header_fmt = endian + ("HHIQQQIHHHHHH" if is_64 else "HHIIIIIHHHHHH")
    header = ident + struct.pack(
        header_fmt,
        3,  # e_type = ET_DYN
        62,  # e_machine
        1,  # e_version
        0,  # e_entry
        0,  # e_phoff
        shoff,
        0,  # e_flags
        header_size,
        0,  # e_phentsize
        0,  # e_phnum
        shdr_size,
        0 if extended_numbering else shnum,
        0xFFFF if extended_numbering else 1,
    )
    assert len(header) == header_size
    return header + shstrtab + symtab + b"".join(shdrs)


def _macho_segment(
    *, is_64: bool, endian: str, name: bytes, section_segnames: tuple[bytes, ...] = ()
) -> bytes:
    """A segment load command, with one section per entry in ``section_segnames``."""
    # 'section_fmt' is (sectname, segname, then the remaining numeric fields)
    if is_64:
        cmd, cmd_fmt, section_fmt, num_numeric_fields = (
            0x19,
            "II16s4Q2i2I",
            "16s16s2Q8I",
            10,
        )
    else:
        cmd, cmd_fmt, section_fmt, num_numeric_fields = (
            0x1,
            "II16s4I2i2I",
            "16s16s9I",
            9,
        )
    num_sections = len(section_segnames)
    cmd_size = struct.calcsize(cmd_fmt) + struct.calcsize(section_fmt) * num_sections
    out = struct.pack(
        endian + cmd_fmt, cmd, cmd_size, name, *([0] * 6), num_sections, 0
    )
    for segname in section_segnames:
        out += struct.pack(
            endian + section_fmt,
            b"__debug_info",
            segname,
            *([0] * num_numeric_fields),
        )
    return out


def _make_thin_macho(
    *,
    is_64: bool = True,
    endian: str = "<",
    segment_names: tuple[bytes, ...] = (b"__TEXT",),
    symbols: tuple[tuple[int, bytes], ...] = ((0x0F, b"_main"),),
    object_file_section_segments: tuple[bytes, ...] = (),
) -> bytes:
    """
    ``symbols`` is a sequence of ``(n_type, name)`` tuples.

    ``object_file_section_segments`` adds an unnamed segment (like in object files)
    containing one section per entry, recording that entry as the section's segment name.
    """
    header_size = 32 if is_64 else 28
    load_commands = b"".join(
        _macho_segment(is_64=is_64, endian=endian, name=name) for name in segment_names
    )
    num_load_commands = len(segment_names) + 1
    if object_file_section_segments:
        load_commands += _macho_segment(
            is_64=is_64,
            endian=endian,
            name=b"",
            section_segnames=object_file_section_segments,
        )
        num_load_commands += 1

    strings, name_offsets = _string_table([name for _, name in symbols])
    nlist_fmt = endian + ("IBBHQ" if is_64 else "IBBhI")
    symtab_cmd_size = 24
    symoff = header_size + len(load_commands) + symtab_cmd_size
    nlists = b"".join(
        struct.pack(nlist_fmt, name_offsets[i], n_type, 0, 0, 0)
        for i, (n_type, _) in enumerate(symbols)
    )
    stroff = symoff + len(nlists)
    load_commands += struct.pack(
        endian + "IIIIII",
        0x2,
        symtab_cmd_size,
        symoff,
        len(symbols),
        stroff,
        len(strings),
    )

    header = struct.pack(
        endian + "IiiIII",
        0xFEEDFACF if is_64 else 0xFEEDFACE,
        0,  # cputype
        0,  # cpusubtype
        6,  # filetype = MH_DYLIB
        num_load_commands,
        len(load_commands),
    )
    header += struct.pack(endian + "I", 0)  # flags
    if is_64:
        header += struct.pack(endian + "I", 0)  # reserved
    assert len(header) == header_size
    return header + load_commands + nlists + strings


def _make_fat_macho(slices: list[bytes], *, is_64: bool = False) -> bytes:
    fat_arch_size = 32 if is_64 else 20
    offset = 8 + fat_arch_size * len(slices)
    fat_arches = b""
    for thin in slices:
        if is_64:
            fat_arches += struct.pack(">iiQQII", 0, 0, offset, len(thin), 0, 0)
        else:
            fat_arches += struct.pack(">iiIII", 0, 0, offset, len(thin), 0)
        offset += len(thin)
    magic = 0xCAFEBABF if is_64 else 0xCAFEBABE
    return struct.pack(">II", magic, len(slices)) + fat_arches + b"".join(slices)


def _make_pe(
    *,
    section_names: tuple[bytes, ...] = (b".text",),
    long_section_names: tuple[bytes, ...] = (),
    symbols: tuple[tuple[int, int], ...] = (),
) -> bytes:
    """
    ``long_section_names`` are stored in the COFF string table.
    ``symbols`` is a sequence of ``(storage_class, num_aux_records)`` tuples.
    """
    e_lfanew = 0x40
    optional_header_size = 0xF0
    num_sections = len(section_names) + len(long_section_names)
    section_table_offset = e_lfanew + 24 + optional_header_size
    symbol_table_offset = section_table_offset + 40 * num_sections

    symbol_table = b""
    num_symbols = 0
    for storage_class, num_aux in symbols:
        symbol_table += struct.pack("<8sIhHBB", b"sym", 0, 0, 0, storage_class, num_aux)
        # aux records that look like '.file' symbols, to check they're skipped
        symbol_table += (b"\0" * 16 + bytes([0x67, 0])) * num_aux
        num_symbols += 1 + num_aux

    long_names = b"".join(name + b"\0" for name in long_section_names)
    string_table = struct.pack("<I", 4 + len(long_names)) + long_names

    section_table = b""
    for name in section_names:
        section_table += struct.pack("<8s32x", name)
    offset = 4
    for name in long_section_names:
        section_table += struct.pack("<8s32x", f"/{offset}".encode())
        offset += len(name) + 1

    dos_header = b"MZ" + b"\0" * 0x3A + struct.pack("<I", e_lfanew)
    coff_header = b"PE\0\0" + struct.pack(
        "<HHIIIHH",
        0x8664,  # machine
        num_sections,
        0,  # timestamp
        symbol_table_offset if symbols or long_section_names else 0,
        num_symbols,
        optional_header_size,
        0x2022,  # characteristics
    )
    optional_header = b"\0" * optional_header_size
    return (
        dos_header
        + coff_header
        + optional_header
        + section_table
        + symbol_table
        + string_table
    )


def _check_bytes(tmp_path, content: bytes) -> tuple[bool, str]:
    lib_file = tmp_path / "lib.so"
    lib_file.write_bytes(content)
    return _file_has_debug_symbols(str(lib_file))


_ELF_VARIANTS = [
    pytest.param(True, "<", id="ELF64-LE"),
    pytest.param(True, ">", id="ELF64-BE"),
    pytest.param(False, "<", id="ELF32-LE"),
    pytest.param(False, ">", id="ELF32-BE"),
]


@pytest.mark.parametrize(("is_64", "endian"), _ELF_VARIANTS)
@pytest.mark.parametrize("debug_section", [b".debug_info", b".zdebug_line"])
def test_elf_debug_sections_detected(tmp_path, is_64, endian, debug_section):
    content = _make_elf(
        is_64=is_64, endian=endian, section_names=(b".text", debug_section)
    )
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS


@pytest.mark.parametrize(("is_64", "endian"), _ELF_VARIANTS)
def test_elf_debugger_only_symbols_detected(tmp_path, is_64, endian):
    content = _make_elf(is_64=is_64, endian=endian, symbol_types=[_STT_FUNC, _STT_FILE])
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SYMBOLS


@pytest.mark.parametrize(("is_64", "endian"), _ELF_VARIANTS)
def test_elf_without_debug_symbols(tmp_path, is_64, endian):
    content = _make_elf(is_64=is_64, endian=endian, symbol_types=[_STT_FUNC])
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_elf_extended_section_numbering(tmp_path):
    content = _make_elf(section_names=(b".debug_info",), extended_numbering=True)
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS


def test_elf_with_huge_section_size(tmp_path):
    content = bytearray(_make_elf(section_names=(b".debug_info",)))
    # set 'sh_size' of '.shstrtab' (section header 1) to 2^63
    shoff = struct.unpack_from("<Q", content, 0x28)[0]
    struct.pack_into("<Q", content, shoff + 64 + 32, 2**63)
    assert _check_bytes(tmp_path, bytes(content)) == _NO_DEBUG_SYMBOLS


def test_elf_without_section_headers(tmp_path):
    content = bytearray(_make_elf(section_names=(b".debug_info",)))
    # zero out the section header table offset (e_shoff)
    content[0x28:0x30] = b"\0" * 8
    assert _check_bytes(tmp_path, bytes(content)) == _NO_DEBUG_SYMBOLS


@pytest.mark.parametrize("is_64", [True, False])
@pytest.mark.parametrize("endian", ["<", ">"])
def test_macho_stab_symbols_detected(tmp_path, is_64, endian):
    content = _make_thin_macho(
        is_64=is_64,
        endian=endian,
        # N_SO stab, naming a source file
        symbols=((0x0F, b"_main"), (0x64, b"/src/main.c")),
    )
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SYMBOLS


def test_macho_strip_symbol_is_ignored(tmp_path):
    content = _make_thin_macho(
        symbols=((0x0F, b"_main"), (0x3C, _MACHO_STRIP_SYMBOL)),
    )
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_macho_dwarf_segment_detected(tmp_path):
    content = _make_thin_macho(segment_names=(b"__TEXT", b"__DWARF"))
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS


@pytest.mark.parametrize("is_64", [True, False])
def test_macho_object_file_dwarf_sections_detected(tmp_path, is_64):
    content = _make_thin_macho(
        is_64=is_64, object_file_section_segments=(b"__TEXT", b"__DWARF")
    )
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS
    content = _make_thin_macho(is_64=is_64, object_file_section_segments=(b"__TEXT",))
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


@pytest.mark.parametrize("is_64", [True, False])
def test_macho_without_debug_symbols(tmp_path, is_64):
    content = _make_thin_macho(is_64=is_64)
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


@pytest.mark.parametrize("is_64", [True, False])
def test_fat_macho_checks_every_slice(tmp_path, is_64):
    clean = _make_thin_macho()
    with_stabs = _make_thin_macho(symbols=((0x64, b"/src/main.c"),))
    assert _check_bytes(
        tmp_path, _make_fat_macho([clean, with_stabs], is_64=is_64)
    ) == (_FOUND_DEBUG_SYMBOLS)
    assert (
        _check_bytes(tmp_path, _make_fat_macho([clean, clean], is_64=is_64))
        == _NO_DEBUG_SYMBOLS
    )


def test_java_class_file_is_not_treated_as_fat_macho(tmp_path):
    # Java .class files share the fat Mach-O magic number (0xCAFEBABE),
    # followed by minor version 0 and major version 61 (Java 17)
    content = struct.pack(">IHH", 0xCAFEBABE, 0, 61) + b"\0" * 2048
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_pe_long_debug_section_names_detected(tmp_path):
    content = _make_pe(long_section_names=(b".debug_info",))
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS


def test_pe_short_debug_section_names_detected(tmp_path):
    content = _make_pe(section_names=(b".text", b".debug_a"))
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SECTIONS


def test_pe_file_symbols_detected(tmp_path):
    # C_EXT symbol, then C_FILE ('.file') symbol with 1 aux record
    content = _make_pe(symbols=((2, 0), (0x67, 1)))
    assert _check_bytes(tmp_path, content) == _FOUND_DEBUG_SYMBOLS


def test_pe_aux_symbol_records_are_skipped(tmp_path):
    # aux records contain the C_FILE value at the storage class position
    content = _make_pe(symbols=((2, 2), (3, 1)))
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_pe_without_debug_symbols(tmp_path):
    content = _make_pe(section_names=(b".text", b".rdata"))
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_dos_executable_without_pe_header(tmp_path):
    content = b"MZ" + b"\0" * 0x3A + struct.pack("<I", 0x40) + b"\0" * 64
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(_make_elf(section_names=(b".debug_info",)), id="ELF"),
        pytest.param(_make_elf(symbol_types=[_STT_FILE]), id="ELF-symtab"),
        pytest.param(_make_thin_macho(symbols=((0x64, b"/src/main.c"),)), id="Mach-O"),
        pytest.param(
            _make_fat_macho([_make_thin_macho(symbols=((0x64, b"/src/main.c"),))]),
            id="Mach-O-fat",
        ),
        pytest.param(_make_pe(long_section_names=(b".debug_info",)), id="PE"),
        pytest.param(_make_pe(symbols=((0x67, 1),)), id="PE-symbols"),
    ],
)
def test_truncated_files_do_not_raise(tmp_path, content):
    assert _check_bytes(tmp_path, content) != _NO_DEBUG_SYMBOLS
    possible_results = {_NO_DEBUG_SYMBOLS, _FOUND_DEBUG_SECTIONS, _FOUND_DEBUG_SYMBOLS}
    for size in range(len(content)):
        assert _check_bytes(tmp_path, content[:size]) in possible_results


def _patched(content: bytes, *, offset: int, fmt: str, value: int) -> bytes:
    out = bytearray(content)
    struct.pack_into(fmt, out, offset, value)
    return bytes(out)


# offsets into the ELF64 files produced by _make_elf()
_ELF_WITH_DEBUG = _make_elf(section_names=(b".text",), symbol_types=[_STT_FILE])
_ELF_SHOFF = struct.unpack_from("<Q", _ELF_WITH_DEBUG, 0x28)[0]
_ELF_SHDR_SIZE = 64
# section headers: (null, .shstrtab, .text, .symtab)
_ELF_TEXT_SHDR = _ELF_SHOFF + 2 * _ELF_SHDR_SIZE
_ELF_SYMTAB_SHDR = _ELF_SHOFF + 3 * _ELF_SHDR_SIZE

# offsets into the 64-bit Mach-O files produced by _make_thin_macho()
_MACHO_WITH_DEBUG = _make_thin_macho(symbols=((0x64, b"/src/main.c"),))
_MACHO_NCMDS = 16
_MACHO_FIRST_CMDSIZE = 32 + 4
_MACHO_OBJECT_FILE = _make_thin_macho(
    symbols=((0x64, b"/src/main.c"),), object_file_section_segments=(b"__TEXT",)
)
# the unnamed segment is the second load command, after one 72-byte segment command
_MACHO_OBJECT_FILE_NSECTS = 32 + 72 + 64


@pytest.mark.parametrize(
    "content",
    [
        pytest.param(
            _patched(_ELF_WITH_DEBUG, offset=4, fmt="B", value=3),
            id="ELF-invalid-class",
        ),
        pytest.param(
            _patched(_ELF_WITH_DEBUG, offset=0x3A, fmt="<H", value=10),
            id="ELF-section-header-too-small",
        ),
        pytest.param(
            _patched(_ELF_WITH_DEBUG, offset=0x3E, fmt="<H", value=50),
            id="ELF-shstrndx-out-of-range",
        ),
        pytest.param(
            _patched(_ELF_WITH_DEBUG, offset=_ELF_TEXT_SHDR, fmt="<I", value=0xFFFF),
            id="ELF-section-name-out-of-range",
        ),
        pytest.param(
            _patched(_ELF_WITH_DEBUG, offset=_ELF_SYMTAB_SHDR + 56, fmt="<Q", value=0),
            id="ELF-symtab-entsize-zero",
        ),
        pytest.param(
            _patched(_MACHO_WITH_DEBUG, offset=_MACHO_NCMDS, fmt="<I", value=100),
            id="Mach-O-too-many-load-commands",
        ),
        pytest.param(
            _patched(_MACHO_WITH_DEBUG, offset=_MACHO_NCMDS, fmt="<I", value=1),
            id="Mach-O-missing-symtab-command",
        ),
        pytest.param(
            _patched(_MACHO_WITH_DEBUG, offset=_MACHO_FIRST_CMDSIZE, fmt="<I", value=0),
            id="Mach-O-load-command-size-zero",
        ),
        pytest.param(
            _patched(
                _MACHO_OBJECT_FILE,
                offset=_MACHO_OBJECT_FILE_NSECTS,
                fmt="<I",
                value=100,
            ),
            id="Mach-O-too-many-sections",
        ),
    ],
)
def test_malformed_headers_are_treated_as_no_debug_symbols(tmp_path, content):
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS


def test_malformed_header_test_inputs_have_debug_symbols_when_not_patched(tmp_path):
    assert _check_bytes(tmp_path, _ELF_WITH_DEBUG) == _FOUND_DEBUG_SYMBOLS
    assert _check_bytes(tmp_path, _MACHO_WITH_DEBUG) == _FOUND_DEBUG_SYMBOLS
    assert _check_bytes(tmp_path, _MACHO_OBJECT_FILE) == _FOUND_DEBUG_SYMBOLS


@pytest.mark.parametrize(
    "content",
    [b"", b"\x7f", b"print('hello')\n", b"\x7fELF" + b"\xff" * 60],
)
def test_other_files_have_no_debug_symbols(tmp_path, content):
    assert _check_bytes(tmp_path, content) == _NO_DEBUG_SYMBOLS
