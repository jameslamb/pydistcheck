"""
Implementations for individual checks that ``pydistcheck``
performs on distributions.
"""

from collections import defaultdict
from typing import List, Protocol

from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.utils import _FileSize

# ALL_CHECKS constant is used to validate configuration options like '--ignore' that reference
# check names. It's a set literal so it doesn't need to be recomputed at runtime, and this project
# relies on unit tests to ensure that it's updated as the list of checks changes.
ALL_CHECKS = {
    "distro-too-large-compressed",
    "distro-too-large-uncompressed",
    "too-many-files",
    "files-only-differ-by-case",
    "path-contains-non-ascii-characters",
    "path-contains-spaces",
}


class _CheckProtocol(Protocol):
    check_name: str

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


class _NonAsciiCharacterCheck(_CheckProtocol):

    check_name = "path-contains-non-ascii-characters"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for file_path in distro_summary.file_paths:
            if not file_path.isascii():
                ascii_converted_str = file_path.encode("ascii", "replace").decode("ascii")
                msg = (
                    f"[{self.check_name}] Found file path containing non-ASCII characters: "
                    f"'{ascii_converted_str}'"
                )
                out.append(msg)
        return out


class _SpacesInPathCheck(_CheckProtocol):

    check_name = "path-contains-spaces"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for file_path in distro_summary.file_paths:
            if file_path != file_path.replace(" ", ""):
                msg = (
                    f"[{self.check_name}] File paths with spaces are not portable. "
                    f"Found path with spaces: '{file_path}'"
                )
                out.append(msg)
        return out
