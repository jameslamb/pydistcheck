import csv
import pathlib
import tarfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class _FileInfo:
    name: str
    file_extension: str
    is_file: bool
    is_directory: bool
    compressed_size_bytes: int

    @classmethod
    def from_tarfile_member(cls, tar_info: tarfile.TarInfo) -> "_FileInfo":
        file_name = tar_info.name
        return cls(
            name=file_name,
            file_extension=pathlib.Path(file_name).suffix or "no-extension",
            is_file=tar_info.isfile(),
            is_directory=tar_info.isdir(),
            compressed_size_bytes=tar_info.size,
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
            compressed_size_bytes=zip_info.file_size,
        )


@dataclass
class _DistributionSummary:
    file_infos: List[_FileInfo]

    @classmethod
    def from_file(self, filename: str) -> "_DistributionSummary":
        if filename.endswith("gz"):
            with tarfile.open(filename, mode="r:gz") as tf:
                file_infos = [_FileInfo.from_tarfile_member(tar_info=m) for m in tf.getmembers()]
        else:
            # assume anything else can be opened with zipfile
            with zipfile.ZipFile(filename, mode="r") as f:
                file_infos = [_FileInfo.from_zipfile_member(zip_info=m) for m in f.infolist()]
        return _DistributionSummary(file_infos=file_infos)

    @property
    def num_directories(self) -> int:
        return sum([1 for f in self.file_infos if f.is_directory])

    @property
    def num_files(self) -> int:
        return sum([1 for f in self.file_infos if f.is_file])

    @property
    def size_by_file_extension(self) -> defaultdict:
        out = defaultdict(int)
        for f in self.file_infos:
            if f.is_file:
                out[f.file_extension] += f.compressed_size_bytes
        return out


def summarize_distribution_contents(file: str, output_file: Optional[str] = None) -> None:
    print(f"checking file '{file}'")

    summary = _DistributionSummary.from_file(filename=file)

    print("contents")
    print(f"  * directories: {summary.num_directories}")
    print(f"  * files: {summary.num_files}")

    if output_file is not None:
        print(f"writing size-by-extension results to '{output_file}'")
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["extension", "size"])
            writer.writeheader()
            for extension, size in summary.size_by_file_extension.items():
                writer.writerow({"extension": extension, "size": size})
        print("done writing CSV")
    else:
        print("sizes")
        for extension, size in summary.size_by_file_extension.items():
            print(f"  * {extension} - {round(size / 1024.0, 1)}K")
