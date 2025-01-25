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
from tempfile import TemporaryDirectory
from typing import Dict, List

from ._file_utils import (
    _ArchiveFormat,
    _decompress_zstd_archive,
    _DirectoryInfo,
    _FileInfo,
    _guess_archive_format,
)


@dataclass
class _DistributionSummary:
    archive_format: str
    compressed_size_bytes: int
    directories: List[_DirectoryInfo]
    files: List[_FileInfo]
    original_file: str

    @classmethod
    def from_file(cls, filename: str) -> "_DistributionSummary":
        archive_format = _guess_archive_format(filename)
        compressed_size_bytes = os.path.getsize(filename)
        directories: List[_DirectoryInfo] = []
        files: List[_FileInfo] = []
        if archive_format == _ArchiveFormat.GZIP_TAR:
            with tarfile.open(filename, mode="r:gz") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        files.append(
                            _FileInfo.from_tarfile_member(
                                archive_file=tf, tar_info=tar_info
                            )
                        )
                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        elif archive_format == _ArchiveFormat.BZIP2_TAR:
            with tarfile.open(filename, mode="r:bz2") as tf:
                for tar_info in tf.getmembers():
                    if tar_info.isfile():
                        files.append(
                            _FileInfo.from_tarfile_member(
                                archive_file=tf, tar_info=tar_info
                            )
                        )
                    else:
                        directories.append(_DirectoryInfo(name=tar_info.name))
        elif archive_format == _ArchiveFormat.CONDA:
            # as of Jan 2023, .conda files are a zip archive containing:
            #   - an uncompressed file 'metadata.json' describing the contents
            #   - 2 zstd-compressed tarfiles with the package contents
            #      - 'info-*.tar.zst'
            #      - 'pkg-*.tar.zst'
            #
            # ref: https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/packages.html#conda-file-format
            with zipfile.ZipFile(
                filename, mode="r"
            ) as f, TemporaryDirectory() as tmp_dir:
                for zip_info in f.infolist():
                    # case 1 - is a directory
                    if zip_info.is_dir():
                        directories.append(_DirectoryInfo(name=zip_info.filename))
                    # case 2 - is a file but not one of the zstandard-compressed ones
                    elif not zip_info.filename.lower().endswith("tar.zst"):
                        files.append(
                            _FileInfo.from_zipfile_member(
                                archive_file=f, zip_info=zip_info
                            )
                        )
                    # case 3 - one of the zstandard-compressed archives
                    else:
                        full_path = os.path.join(tmp_dir, zip_info.filename)
                        # ref: https://stackoverflow.com/a/55260983/3986677
                        #
                        # decompress and write to a regular tarfile
                        with zipfile.ZipFile(filename, mode="r") as zf:
                            zf.extractall(path=tmp_dir, members=[zip_info.filename])

                            # decompress the .tar.zst to just .tar
                            decompressed_tar_path = full_path.lower().replace(
                                ".tar.zst", ".tar"
                            )
                            _decompress_zstd_archive(
                                tar_zst_file=full_path,
                                decompressed_tar_path=decompressed_tar_path,
                            )

                        # do tarfile things
                        with tarfile.open(decompressed_tar_path, mode="r") as tf:
                            for tar_info in tf.getmembers():
                                if tar_info.isfile():
                                    files.append(
                                        _FileInfo.from_tarfile_member(
                                            archive_file=tf, tar_info=tar_info
                                        )
                                    )
                                else:
                                    directories.append(
                                        _DirectoryInfo(name=tar_info.name)
                                    )
        elif archive_format == _ArchiveFormat.ZIP:
            # assume anything else can be opened with zipfile
            with zipfile.ZipFile(filename, mode="r") as f:
                for zip_info in f.infolist():
                    if not zip_info.is_dir():
                        files.append(
                            _FileInfo.from_zipfile_member(
                                archive_file=f, zip_info=zip_info
                            )
                        )
                    else:
                        directories.append(_DirectoryInfo(name=zip_info.filename))

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
        return sorted(
            self.files, key=lambda f: f.uncompressed_size_bytes, reverse=True
        )[:n]

    @property
    def uncompressed_size_bytes(self) -> int:
        return sum(f.uncompressed_size_bytes for f in self.files)

    @property
    def size_by_file_extension(self) -> "OrderedDict[str, int]":
        """
        Aggregate file sizes in a distribution by extension.

        :return: An OrderedDict where keys are file extensions and values are the total size in
                 bytes (uncompressed) occupied by such files in the distribution.
                 Sorted in descending order by size.
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
