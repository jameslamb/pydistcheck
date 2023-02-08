"""
Code that prints diagnostic information about a distribution.
"""

from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.utils import _FileSize


def inspect_distribution(filepath: str) -> None:
    summary = _DistributionSummary.from_file(filename=filepath)
    print("file size")
    compressed_size = _FileSize(summary.compressed_size_bytes, "B")
    uncompressed_size = _FileSize(summary.uncompressed_size_bytes, "B")
    print(f"  * compressed size: {compressed_size}")
    print(f"  * uncompressed size: {uncompressed_size}")
    space_saving = 1.0 - (compressed_size.total_size_bytes / uncompressed_size.total_size_bytes)
    print(f"  * compression space saving: {round(100 * space_saving, 1)}%")

    print("contents")
    print(f"  * directories: {summary.num_directories}")
    print(f"  * files: {summary.num_files} ({len(summary.compiled_objects)} compiled)")

    print("size by extension")
    for extension, size in summary.size_by_file_extension.items():
        size_pct = size / summary.uncompressed_size_bytes
        print(f"  * {extension} - {round(size / 1024.0, 1)}K ({round(size_pct * 100, 1)}%)")
