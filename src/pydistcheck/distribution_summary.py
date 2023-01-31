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
from tempfile import TemporaryFile
from typing import List
from _vendored_delocate import _is_macho_file

# TODO: detect file format without relying on file extension?
#
# https://www.netspi.com/blog/technical/web-application-penetration-testing/magic-bytes-identifying-common-file-formats-at-a-glance/
# https://www.garykessler.net/library/file_sigs.html
_COMPILED_OBJECT_EXTENSIONS = {".dll", ".dylib", ".o", ".so"}


# ref: https://en.wikipedia.org/wiki/List_of_file_signatures
_ELF_MAGIC = {
    0x7F454C46.to_bytes(4, "little"),
    0x7F454C46.to_bytes(4, "big"),
}
def _is_elf_file(filename: str) -> bool:
    """detect ELF files (.so, .o)"""
    try:
        with open(filename, "rb") as f:
            header = f.read(4)
            return header in _ELF_MAGIC
    except PermissionError:  # pragma: no cover
        return False
    except FileNotFoundError:  # pragma: no cover
        return False


_DOS_MZ_MAGIC = {
    0x4D5A.to_bytes(4, "little"),
}
def _is_dos_mz_executable(filename: str) -> bool:
    """detect Windows Portable Executable (e.g. .dll, .exe)"""
    try:
        with open(filename, "rb") as f:
            header = f.read(4)
            return header in _DOS_MZ_MAGIC
    except PermissionError:  # pragma: no cover
        return False
    except FileNotFoundError:  # pragma: no cover
        return False


@dataclass
class _DirectoryInfo:
    name: str


@dataclass
class _FileInfo:
    name: str
    file_extension: str
    uncompressed_size_bytes: int

    @classmethod
    def from_tarfile_member(cls, tar_info: tarfile.TarInfo) -> "_FileInfo":
        file_name = tar_info.name
        return cls(
            name=file_name,
            file_extension=pathlib.Path(file_name).suffix or "no-extension",
            uncompressed_size_bytes=tar_info.size,
        )

    @classmethod
    def from_zipfile_member(cls, zip_info: zipfile.ZipInfo) -> "_FileInfo":
        file_name = zip_info.filename
        return cls(
            name=file_name,
            file_extension=pathlib.Path(file_name).suffix or "no-extension",
            uncompressed_size_bytes=zip_info.file_size,
        )


_MAX_TAR_MEMBER_SIZE_BYTES = 250 * 1024 * 1024


def _archive_member_is_compiled_object(
    archive_file: Union[tarfile.TarFile, zipfile.ZipFile],
    member_name: str
) -> bool:
    if isinstance(archive_file, zipfile.ZipFile):
        with archive_file.open(name=member_name, mode="r") as f:
            header = f.read(4)
    else:
        with TemporaryFile() as f:
            archive_file.extract(member=member_name, path=f)
            header = f.read(4)




@dataclass
class _DistributionSummary:
    compiled_objects: List[_FileInfo]
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
            with tarfile.open(filename, mode="r:gz") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        files.append(_FileInfo.from_tarfile_member(tar_info))

                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        else:
            # assume anything else can be opened with zipfile
            with zipfile.ZipFile(filename, mode="r") as f:
                for zip_info in f.infolist():
                    if not zip_info.is_dir():
                        files.append(_FileInfo.from_zipfile_member(zip_info))
                    else:
                        directories.append(_DirectoryInfo(name=zip_info.filename))
        compiled_objects = [
            file_info
            for file_info in files
            if file_info.file_extension in _COMPILED_OBJECT_EXTENSIONS
        ]

        return cls(
            compiled_objects=compiled_objects,
            compressed_size_bytes=compressed_size_bytes,
            directories=directories,
            files=files,
            original_file=filename,
        )

    @property
    def all_paths(self) -> List[str]:
        return self.file_paths + self.directory_paths

    @property
    def directory_paths(self) -> List[str]:
        return [d.name for d in self.directories]

    @property
    def file_paths(self) -> List[str]:
        return [f.name for f in self.files]

    @property
    def num_directories(self) -> int:
        return len(self.directories)

    @property
    def num_files(self) -> int:
        return len(self.files)

    @property
    def uncompressed_size_bytes(self) -> int:
        return sum(f.uncompressed_size_bytes for f in self.files)

    @property
    def size_by_file_extension(self) -> OrderedDict:
        """
        Aggregate file sizes in a distribution by extension.

        :return: An OrderedDict where keys are file extensions and values are the total size in
                 bytes occupied by such files in the distribution. Sorted in descending
                 order by size.
        """
        summary_dict: defaultdict = defaultdict(int)
        for f in self.files:
            summary_dict[f.file_extension] += f.uncompressed_size_bytes
        sorted_sizes = list(summary_dict.items())
        sorted_sizes.sort(key=lambda x: x[1], reverse=True)
        out = OrderedDict()
        for file_extension, size_in_bytes in sorted_sizes:
            out[file_extension] = size_in_bytes
        return out
