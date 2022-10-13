from typing import List
from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.utils import _FileSize


class _DistroTooLargeCompressedCheck:

    check_name = "distro-too-large-compressed"

    def __init__(self, max_allowed_size_bytes: int):
        self.max_allowed_size_bytes = max_allowed_size_bytes

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        max_size = _FileSize(num=self.max_allowed_size_bytes, unit_str="B")
        actual_size = _FileSize(num=distro_summary.total_size_in_bytes_compressed, unit_str="B")
        if actual_size > max_size:
            msg = f"[{self.check_name}] Size {actual_size} is larger than the allowed size ({max_size})."
            out.append(msg)
        return out


class _FileCountCheck:

    check_name = "too-many-files"

    def __init__(self, max_allowed_files: int):
        self.max_allowed_files = max_allowed_files

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        num_files = distro_summary.num_files
        if num_files > self.max_allowed_files:
            msg = f"[{self.check_name}] Found {num_files} files. Only {self.max_allowed_files} allowed."
            out.append(msg)
        return out
