import pathlib
import tarfile
import zipfile
from dataclasses import dataclass
from typing import Tuple, Union


@dataclass
class _DirectoryInfo:
    name: str


class _ArchiveFormat:
    BZIP2_TAR = ".tar.bz2"
    CONDA = ".conda"
    GZIP_TAR = ".tar.gz"
    ZIP = ".zip"


def _guess_archive_format(filename: str) -> str:
    if filename.endswith("gz"):
        return _ArchiveFormat.GZIP_TAR
    if filename.endswith("bz2"):
        return _ArchiveFormat.BZIP2_TAR
    if filename.endswith(".conda"):
        return _ArchiveFormat.CONDA

    return _ArchiveFormat.ZIP


@dataclass
class _FileInfo:
    name: str
    file_format: str
    file_extension: str
    is_compiled: bool
    uncompressed_size_bytes: int

    @classmethod
    def from_tarfile_member(
        cls, archive_file: tarfile.TarFile, tar_info: tarfile.TarInfo
    ) -> "_FileInfo":
        member_name = tar_info.name
        file_format, is_compiled = _guess_archive_member_file_format(
            archive_file=archive_file, member_name=member_name
        )
        return cls(
            name=member_name,
            file_format=file_format,
            file_extension=pathlib.Path(member_name).suffix or "no-extension",
            is_compiled=is_compiled,
            uncompressed_size_bytes=tar_info.size,
        )

    @classmethod
    def from_zipfile_member(
        cls, archive_file: zipfile.ZipFile, zip_info: zipfile.ZipInfo
    ) -> "_FileInfo":
        member_name = zip_info.filename
        file_format, is_compiled = _guess_archive_member_file_format(
            archive_file=archive_file, member_name=member_name
        )
        return cls(
            name=member_name,
            file_format=file_format,
            file_extension=pathlib.Path(member_name).suffix or "no-extension",
            is_compiled=is_compiled,
            uncompressed_size_bytes=zip_info.file_size,
        )


# references:
#   * https://en.wikipedia.org/wiki/List_of_file_signatures
#   * https://github.com/apple-oss-distributions/xnu/blob/5c2921b07a2480ab43ec66f5b9e41cb872bc554f/EXTERNAL_HEADERS/mach-o/loader.h#L65
#   * https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/fat.h#L48
#   * https://github.com/matthew-brett/delocate/blob/df86dddd7c94a93b5c03948b8c127ba0777e2a4d/delocate/tools.py#L166
#   * https://learn.microsoft.com/en-us/previous-versions/ms809762(v=msdn.10)
#   * https://en.wikipedia.org/wiki/Portable_Executable

# DOS MZ (.dll, .exe)
_DOS_MZ_MAGIC_FIRST_2_BYTES = {
    0x5A4D.to_bytes(2, "little"),
}

# ELF (.so, .o)
_ELF_MAGIC_FIRST_4_BYTES = {
    0x7F454C46.to_bytes(4, "little"),
    0x7F454C46.to_bytes(4, "big"),
}

# MACH-O (.dylib)
_MACH_O_MAGIC_FIRST_4_BYTES = {
    0xFEEDFACE.to_bytes(4, "little"),  # 32-bit
    0xFEEDFACE.to_bytes(4, "big"),  # 32-bit
    0xFEEDFACF.to_bytes(4, "little"),  # 64-bit
    0xFEEDFACF.to_bytes(4, "big"),  # 64-bit
    0xCAFEBABE.to_bytes(4, "big"),  # mach-o fat binary
    0xCAFEBABF.to_bytes(4, "big"),  # mach-o fat binary
}


class _FileFormat:
    ELF = "ELF"
    MACH_O = "Mach-O"
    OTHER = "Other"
    WINDOWS_PE = "Windows PE"


def _guess_archive_member_file_format(
    archive_file: Union[tarfile.TarFile, zipfile.ZipFile], member_name: str
) -> Tuple[str, bool]:
    """
    The approach in this function was inspired by similar code in
    https://github.com/matthew-brett/delocate, so that project's license is included
    in distributions of ``pydistcheck`` at path ``LICENSES/DELOCATE_LICENSE``.

    Returns a two-item tuple of the form ``(file_format, is_compiled)``.
    """
    if isinstance(archive_file, zipfile.ZipFile):
        with archive_file.open(name=member_name, mode="r") as f:
            header = f.read(4)
    else:
        fileobj = archive_file.extractfile(member_name)
        assert fileobj is not None, (
            f"'{member_name}' not found. This is a bug in pydistcheck."
            "Report it at https://github.com/jameslamb/pydistcheck/issues."
        )
        header = fileobj.read(4)

    if header in _ELF_MAGIC_FIRST_4_BYTES:
        return _FileFormat.ELF, True
    if header in _MACH_O_MAGIC_FIRST_4_BYTES:
        return _FileFormat.MACH_O, True
    if header[:2] in _DOS_MZ_MAGIC_FIRST_2_BYTES:
        return _FileFormat.WINDOWS_PE, True

    return _FileFormat.OTHER, False
