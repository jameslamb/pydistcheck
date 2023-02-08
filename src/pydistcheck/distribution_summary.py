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
from typing import List, Union


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


# references:
#   * https://en.wikipedia.org/wiki/List_of_file_signatures
#   * https://github.com/apple-oss-distributions/xnu/blob/5c2921b07a2480ab43ec66f5b9e41cb872bc554f/EXTERNAL_HEADERS/mach-o/loader.h#L65
#   * https://github.com/apple-oss-distributions/cctools/blob/658da8c66b4e184458f9c810deca9f6428a773a5/include/mach-o/fat.h#L48
#   * https://github.com/matthew-brett/delocate/blob/df86dddd7c94a93b5c03948b8c127ba0777e2a4d/delocate/tools.py#L166
#
# This approach was inspired by similar code in https://github.com/matthew-brett/delocate, so that
# project's license is included here in LICENSES/DELOCATE_LICENSE
_MAGIC_FIRST_2_BYTES_FOR_COMPILED_OBJECTS = {
    0x4D5A.to_bytes(4, "little"),  # DOS MZ (.dll, .exe)
}


_MAGIC_FIRST_4_BYTES_FOR_COMPILED_OBJECTS = {
    0x7F454C46.to_bytes(4, "little"),  # ELF (.so, .o)
    0x7F454C46.to_bytes(4, "big"),  # ELF (.so, .o)
    0xFEEDFACE.to_bytes(4, "little"),  # mach-o (.dylib)
    0xFEEDFACE.to_bytes(4, "big"),  # mach-o (.dylib)
    0xFEEDFACF.to_bytes(4, "little"),  # mach-o (.dylib)
    0xFEEDFACF.to_bytes(4, "big"),  # mach-o (.dylib)
    0xCAFEBABE.to_bytes(4, "big"),  # mach-o (.dylib)
    0xCAFEBABF.to_bytes(4, "big"),  # mach-o (.dylib)
}


def _archive_member_is_compiled_object(
    archive_file: Union[tarfile.TarFile, zipfile.ZipFile], member_name: str
) -> bool:
    if isinstance(archive_file, zipfile.ZipFile):
        with archive_file.open(name=member_name, mode="r") as f:
            header = f.read(4)
    else:
        header = archive_file.extractfile(member_name).read(4)

    return (
        header in _MAGIC_FIRST_4_BYTES_FOR_COMPILED_OBJECTS
        or header[:2] in _MAGIC_FIRST_2_BYTES_FOR_COMPILED_OBJECTS
    )


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
        compiled_objects: List[_FileInfo] = []
        if filename.endswith("gz"):
            with tarfile.open(filename, mode="r:gz") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        file_info = _FileInfo.from_tarfile_member(tar_info)
                        files.append(file_info)
                        if _archive_member_is_compiled_object(
                            archive_file=tf, member_name=tar_info.name
                        ):
                            compiled_objects.append(file_info)
                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        else:
            # assume anything else can be opened with zipfile
            with zipfile.ZipFile(filename, mode="r") as f:
                for zip_info in f.infolist():
                    if not zip_info.is_dir():
                        file_info = _FileInfo.from_zipfile_member(zip_info)
                        files.append(file_info)
                        if _archive_member_is_compiled_object(
                            archive_file=f, member_name=zip_info.filename
                        ):
                            compiled_objects.append(file_info)
                    else:
                        directories.append(_DirectoryInfo(name=zip_info.filename))

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
