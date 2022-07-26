import csv
import pathlib
import tarfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass
from typing import Optional


@dataclass
class _DistributionSummary:
    num_files: int
    num_directories: int
    size_by_file_extension: defaultdict


def _get_gzip_summary(file: str) -> _DistributionSummary:
    size_by_file_extension = defaultdict(int)

    with tarfile.open(file, mode="r:gz") as tf:
        all_members = tf.getmembers()

        num_files = 0
        num_directories = 0
        for i, member in enumerate(all_members):
            if member.isfile():
                num_files += 1
                file_name = member.name
                file_extension = pathlib.Path(file_name).suffix
                compressed_size_in_bytes = member.size
                if file_extension == "":
                    file_extension = "no-extension"
                size_by_file_extension[file_extension] += compressed_size_in_bytes
            elif member.isdir():
                num_directories += 1
            else:
                raise ValueError(f"member '{member.name}'' is not a file or directory")

    return _DistributionSummary(
        num_files=num_files,
        num_directories=num_directories,
        size_by_file_extension=size_by_file_extension,
    )


def _get_zipfile_summary(file: str) -> _DistributionSummary:
    size_by_file_extension = defaultdict(int)

    with zipfile.ZipFile(file, mode="r") as f:
        all_members = f.infolist()

        num_files = 0
        num_directories = 0
        for i, member in enumerate(all_members):
            if member.is_dir():
                num_directories += 1
            else:
                num_files += 1
                file_name = member.filename
                file_extension = pathlib.Path(file_name).suffix
                compressed_size_in_bytes = member.file_size
                if file_extension == "":
                    file_extension = "no-extension"
                size_by_file_extension[file_extension] += compressed_size_in_bytes

    return _DistributionSummary(
        num_files=num_files,
        num_directories=num_directories,
        size_by_file_extension=size_by_file_extension,
    )


def summarize_distribution_contents(file: str, output_file: Optional[str] = None) -> None:
    print(f"checking file '{file}'")

    if file.endswith("gz"):
        summary = _get_gzip_summary(file=file)
    else:
        summary = _get_zipfile_summary(file=file)

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
