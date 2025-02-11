"""
Code that prints diagnostic information about a distribution.
"""

from typing import TYPE_CHECKING

from ._utils import _FileSize

if TYPE_CHECKING:
    from ._config import _Config
    from .distribution_summary import _DistributionSummary


def inspect_distribution(*, summary: "_DistributionSummary", config: "_Config") -> None:
    print("file size")
    unit_str = config.output_file_size_unit
    compressed_size = _FileSize(
        num=summary.compressed_size_bytes,
        unit_str="B",
    )
    compressed_size_str = compressed_size.to_string(
        precision=config.output_file_size_precision,
        unit_str=unit_str,
    )
    uncompressed_size = _FileSize(
        num=summary.uncompressed_size_bytes,
        unit_str="B",
    )
    uncompressed_size_str = uncompressed_size.to_string(
        precision=config.output_file_size_precision,
        unit_str=unit_str,
    )
    print(f"  * compressed size: {compressed_size_str}")
    print(f"  * uncompressed size: {uncompressed_size_str}")
    space_saving = 1.0 - (
        compressed_size.total_size_bytes / uncompressed_size.total_size_bytes
    )
    print(f"  * compression space saving: {round(100 * space_saving, 1)}%")

    print("contents")
    print(f"  * directories: {summary.num_directories}")
    print(f"  * files: {summary.num_files} ({len(summary.compiled_objects)} compiled)")

    print("size by extension")
    for extension, size in summary.size_by_file_extension.items():
        size_pct = size / summary.uncompressed_size_bytes
        size_str = _FileSize(
            num=size,
            unit_str="B",
        ).to_string(precision=config.output_file_size_precision, unit_str=unit_str)
        print(f"  * {extension} - {size_str} ({round(size_pct * 100, 1)}%)")

    largest_files = summary.get_largest_files(n=5)
    print("largest files")
    for file_info in largest_files:
        size_str = _FileSize(
            num=file_info.uncompressed_size_bytes,
            unit_str="B",
        ).to_string(precision=config.output_file_size_precision, unit_str=unit_str)
        print(f"  * ({size_str}) {file_info.name}")
