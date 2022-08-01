from typing import List
from pydistcheck.distribution_summary import _DistributionSummary


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
