"""
internal-only classes used to manage information about
source distributions and their contents
"""

import os
import pathlib
import tarfile
import zipfile
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List, Tuple, Union


@dataclass
class _DirectoryInfo:
    name: str


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


class _ArchiveFormat:
    GZIP_TAR = ".tar.gz"
    ZIP = ".zip"


@dataclass
class _DistributionSummary:
    archive_format: str
    compressed_size_bytes: int
    directories: List[_DirectoryInfo]
    files: List[_FileInfo]
    original_file: str

    @classmethod
    def from_file(cls, filename: str) -> "_DistributionSummary":
        compressed_size_bytes = os.path.getsize(filename)
        directories: List[_DirectoryInfo] = []
        files: List[_FileInfo] = []

        if filename.endswith("gz"):
            archive_format = _ArchiveFormat.GZIP_TAR
        else:
            archive_format = _ArchiveFormat.ZIP

        if archive_format == _ArchiveFormat.GZIP_TAR:
            with tarfile.open(filename, mode="r:gz") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        files.append(
                            _FileInfo.from_tarfile_member(archive_file=tf, tar_info=tar_info)
                        )
                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        elif archive_format == _ArchiveFormat.ZIP:
            with zipfile.ZipFile(filename, mode="r") as f:
                for zip_info in f.infolist():
                    if not zip_info.is_dir():
                        files.append(
                            _FileInfo.from_zipfile_member(archive_file=f, zip_info=zip_info)
                        )
                    else:
                        directories.append(_DirectoryInfo(name=zip_info.filename))
        else:
            raise ValueError(
                f"File '{filename}' does not appear to be a Python package distribution in "
                "one of the formats supported by 'pydistcheck'. "
                "Supported formats: .tar.gz, .zip"
            )

        return cls(
            archive_format=archive_format,
            compressed_size_bytes=compressed_size_bytes,
            directories=directories,
            files=files,
            original_file=filename,
        )

    @property
    def all_paths(self) -> List[str]:
        return self.file_paths + self.directory_paths

    @property
    def compiled_objects(self) -> List[_FileInfo]:
        return [f for f in self.files if f.is_compiled is True]

    @cached_property
    def count_by_file_extension(self) -> Dict[str, int]:
        return {
            file_extension: len(file_list)
            for file_extension, file_list in self.files_by_extension.items()
        }

    @property
    def directory_paths(self) -> List[str]:
        return [d.name for d in self.directories]

    @cached_property
    def files_by_extension(self) -> Dict[str, List[_FileInfo]]:
        out: Dict[str, List[_FileInfo]] = defaultdict(list)
        for f in self.files:
            out[f.file_extension].append(f)
        return out

    @property
    def file_paths(self) -> List[str]:
        return [f.name for f in self.files]

    @property
    def num_directories(self) -> int:
        return len(self.directories)

    @property
    def num_files(self) -> int:
        return len(self.files)

    def get_largest_files(self, n: int) -> List[_FileInfo]:
        return sorted(self.files, key=lambda f: f.uncompressed_size_bytes, reverse=True)[:n]

    @property
    def uncompressed_size_bytes(self) -> int:
        return sum(f.uncompressed_size_bytes for f in self.files)

    @property
    def size_by_file_extension(self) -> "OrderedDict[str, int]":
        """
        Aggregate file sizes in a distribution by extension.

        :return: An OrderedDict where keys are file extensions and values are the total size in
                 bytes occupied by such files in the distribution. Sorted in descending
                 order by size.
        """
        summary_dict = {
            file_extension: sum(f.uncompressed_size_bytes for f in files)
            for file_extension, files in self.files_by_extension.items()
        }
        sorted_sizes = list(summary_dict.items())
        sorted_sizes.sort(key=lambda x: x[1], reverse=True)
        out = OrderedDict()
        for file_extension, size_in_bytes in sorted_sizes:
            out[file_extension] = size_in_bytes
        return out
