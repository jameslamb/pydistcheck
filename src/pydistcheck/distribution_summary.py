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
from typing import List


@dataclass
class _FileInfo:
    name: str
    file_extension: str
    is_file: bool
    is_directory: bool
    uncompressed_size_bytes: int

    @classmethod
    def from_tarfile_member(cls, tar_info: tarfile.TarInfo) -> "_FileInfo":
        file_name = tar_info.name
        return cls(
            name=file_name,
            file_extension=pathlib.Path(file_name).suffix or "no-extension",
            is_file=tar_info.isfile(),
            is_directory=tar_info.isdir(),
            uncompressed_size_bytes=tar_info.size,
        )

    @classmethod
    def from_zipfile_member(cls, zip_info: zipfile.ZipInfo) -> "_FileInfo":
        file_name = zip_info.filename
        is_directory = zip_info.is_dir()
        return cls(
            name=file_name,
            file_extension=pathlib.Path(file_name).suffix or "no-extension",
            is_file=not is_directory,
            is_directory=is_directory,
            uncompressed_size_bytes=zip_info.file_size,
        )


@dataclass
class _DistributionSummary:
    compressed_size_bytes: int
    file_infos: List[_FileInfo]

    @classmethod
    def from_file(cls, filename: str) -> "_DistributionSummary":
        compressed_size_bytes = os.path.getsize(filename)
        if filename.endswith("gz"):
            with tarfile.open(filename, mode="r:gz") as tf:
                file_infos = [_FileInfo.from_tarfile_member(tar_info=m) for m in tf.getmembers()]
        else:
            # assume anything else can be opened with zipfile
            with zipfile.ZipFile(filename, mode="r") as f:
                file_infos = [_FileInfo.from_zipfile_member(zip_info=m) for m in f.infolist()]
        return cls(compressed_size_bytes=compressed_size_bytes, file_infos=file_infos)

    @property
    def num_directories(self) -> int:
        return sum(1 for f in self.file_infos if f.is_directory)

    @property
    def num_files(self) -> int:
        return sum(1 for f in self.file_infos if f.is_file)

    @property
    def uncompressed_size_bytes(self) -> int:
        return sum(f.uncompressed_size_bytes for f in self.file_infos)

    @property
    def size_by_file_extension(self) -> OrderedDict:
        """
        Aggregate file sizes in a distribution by extension.

        :return: An OrderedDict where keys are file extensions and values are the total size in
                 bytes occupied by such files in the distribution. Sorted in descending
                 order by size.
        """
        summary_dict: defaultdict = defaultdict(int)
        for f in self.file_infos:
            if f.is_file:
                summary_dict[f.file_extension] += f.uncompressed_size_bytes
        sorted_sizes = list(summary_dict.items())
        sorted_sizes.sort(key=lambda x: x[1], reverse=True)
        out = OrderedDict()
        for file_extension, size_in_bytes in sorted_sizes:
            out[file_extension] = size_in_bytes
        return out
