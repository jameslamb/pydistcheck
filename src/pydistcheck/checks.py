"""
Implementations for individual checks that ``pydistcheck``
performs on distributions.
"""

from collections import defaultdict
from typing import List, Protocol

from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.utils import _FileSize


class _CheckProtocol(Protocol):
    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:  # pragma: no cover
        ...


class _DistroTooLargeCompressedCheck(_CheckProtocol):

    check_name = "distro-too-large-compressed"

    def __init__(self, max_allowed_size_bytes: int):
        self.max_allowed_size_bytes = max_allowed_size_bytes

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        max_size = _FileSize(num=self.max_allowed_size_bytes, unit_str="B")
        actual_size = _FileSize(num=distro_summary.compressed_size_bytes, unit_str="B")
        if actual_size > max_size:
            msg = (
                f"[{self.check_name}] Compressed size {actual_size} is larger "
                f"than the allowed size ({max_size})."
            )
            out.append(msg)
        return out


class _DistroTooLargeUnCompressedCheck(_CheckProtocol):

    check_name = "distro-too-large-uncompressed"

    def __init__(self, max_allowed_size_bytes: int):
        self.max_allowed_size_bytes = max_allowed_size_bytes

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        max_size = _FileSize(num=self.max_allowed_size_bytes, unit_str="B")
        actual_size = _FileSize(num=distro_summary.uncompressed_size_bytes, unit_str="B")
        if actual_size > max_size:
            msg = (
                f"[{self.check_name}] Uncompressed size {actual_size} is larger "
                f"than the allowed size ({max_size})."
            )
            out.append(msg)
        return out


class _FileCountCheck(_CheckProtocol):

    check_name = "too-many-files"

    def __init__(self, max_allowed_files: int):
        self.max_allowed_files = max_allowed_files

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        num_files = distro_summary.num_files
        if num_files > self.max_allowed_files:
            msg = (
                f"[{self.check_name}] Found {num_files} files. "
                f"Only {self.max_allowed_files} allowed."
            )
            out.append(msg)
        return out


class _FilesOnlyDifferByCaseCheck(_CheckProtocol):

    check_name = "files-only-differ-by-case"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        path_lower_to_raw = defaultdict(list)
        for file_info in distro_summary.file_infos:
            path_lower_to_raw[file_info.name.lower()].append(file_info.name)

        duplicates_list: List[str] = []
        for _, filepaths in path_lower_to_raw.items():
            if len(filepaths) > 1:
                duplicates_list += filepaths

        if duplicates_list:
            duplicates_str = ",".join(duplicates_list)
            msg = (
                f"[{self.check_name}] Found files which differ only by case. "
                "Such files are not portable, since some filesystems are case-insensitive. "
                f"Files: {duplicates_str}"
            )
            out.append(msg)
        return out
