"""
internal-only classes used to manage information about
source distributions and their contents
"""

import os
import tarfile
import zipfile
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from functools import cached_property
from typing import Dict, List

from .file_utils import _ArchiveFormat, _FileInfo, _guess_archive_format


@dataclass
class _DirectoryInfo:
    name: str


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

        archive_format = _guess_archive_format(filename)

        if archive_format == _ArchiveFormat.GZIP_TAR:
            with tarfile.open(filename, mode="r:gz") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        files.append(
                            _FileInfo.from_tarfile_member(archive_file=tf, tar_info=tar_info)
                        )
                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        elif archive_format == _ArchiveFormat.BZIP2_TAR:
            with tarfile.open(filename, mode="r:bz2") as tf:
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
