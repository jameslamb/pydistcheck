"""
Implementations for individual checks that ``pydistcheck``
performs on distributions.
"""

import os
from collections import defaultdict
from fnmatch import fnmatchcase
from tempfile import TemporaryDirectory
from typing import List, Protocol, Sequence

from ._distribution_summary import _DistributionSummary
from ._file_utils import _extract_subset_of_files_from_archive
from ._shared_lib_utils import _file_has_debug_symbols
from ._utils import _FileSize

# ALL_CHECKS constant is used to validate configuration options like '--ignore' that reference
# check names. It's a set literal so it doesn't need to be recomputed at runtime, and this project
# relies on unit tests to ensure that it's updated as the list of checks changes.
ALL_CHECKS = {
    "compiled-objects-have-debug-symbols",
    "distro-too-large-compressed",
    "distro-too-large-uncompressed",
    "expected-files",
    "too-many-files",
    "files-only-differ-by-case",
    "mixed-file-extensions",
    "path-contains-non-ascii-characters",
    "path-contains-spaces",
    "path-too-long",
    "unexpected-files",
}


class _CheckProtocol(Protocol):
    check_name: str

    def __call__(
        self, distro_summary: _DistributionSummary
    ) -> List[str]:  # pragma: no cover
        ...


class _CompiledObjectsDebugSymbolCheck(_CheckProtocol):
    check_name = "compiled-objects-have-debug-symbols"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        compiled_object_paths = [
            file_info.name for file_info in distro_summary.compiled_objects
        ]
        if not compiled_object_paths:
            return out

        with TemporaryDirectory() as tmp_dir:
            _extract_subset_of_files_from_archive(
                archive_file=distro_summary.original_file,
                archive_format=distro_summary.archive_format,
                relative_paths=compiled_object_paths,
                out_dir=tmp_dir,
            )

            for file_relative_path in compiled_object_paths:
                has_debug_symbols, cmd_str = _file_has_debug_symbols(
                    file_absolute_path=os.path.join(tmp_dir, file_relative_path)
                )
                if has_debug_symbols:
                    msg = (
                        f"[{self.check_name}] Found compiled object containing debug symbols. "
                        "For details, extract the distribution contents and run "
                        f"'{cmd_str} \"{file_relative_path}\"'."
                    )
                    out.append(msg)
        return out


class _DistroTooLargeCompressedCheck(_CheckProtocol):
    check_name = "distro-too-large-compressed"

    def __init__(
        self,
        *,
        max_allowed_size_bytes: int,
        output_file_size_precision: int,
        output_file_size_unit: str,
    ):
        self.max_allowed_size_bytes = max_allowed_size_bytes
        self.output_file_size_precision = output_file_size_precision
        self.output_file_size_unit = output_file_size_unit

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        max_size = _FileSize(num=self.max_allowed_size_bytes, unit_str="B")
        actual_size = _FileSize(num=distro_summary.compressed_size_bytes, unit_str="B")
        if actual_size > max_size:
            actual_size_str = actual_size.to_string(
                precision=self.output_file_size_precision,
                unit_str=self.output_file_size_unit,
            )
            max_size_str = max_size.to_string(
                precision=self.output_file_size_precision,
                unit_str=self.output_file_size_unit,
            )
            msg = (
                f"[{self.check_name}] Compressed size {actual_size_str} is larger "
                f"than the allowed size ({max_size_str})."
            )
            out.append(msg)
        return out


class _DistroTooLargeUnCompressedCheck(_CheckProtocol):
    check_name = "distro-too-large-uncompressed"

    def __init__(
        self,
        *,
        max_allowed_size_bytes: int,
        output_file_size_precision: int,
        output_file_size_unit: str,
    ):
        self.max_allowed_size_bytes = max_allowed_size_bytes
        self.output_file_size_precision = output_file_size_precision
        self.output_file_size_unit = output_file_size_unit

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        max_size = _FileSize(num=self.max_allowed_size_bytes, unit_str="B")
        actual_size = _FileSize(
            num=distro_summary.uncompressed_size_bytes, unit_str="B"
        )
        if actual_size > max_size:
            actual_size_str = actual_size.to_string(
                precision=self.output_file_size_precision,
                unit_str=self.output_file_size_unit,
            )
            max_size_str = max_size.to_string(
                precision=self.output_file_size_precision,
                unit_str=self.output_file_size_unit,
            )
            msg = (
                f"[{self.check_name}] Uncompressed size {actual_size_str} is larger "
                f"than the allowed size ({max_size_str})."
            )
            out.append(msg)
        return out


class _FileCountCheck(_CheckProtocol):
    check_name = "too-many-files"

    def __init__(self, *, max_allowed_files: int):
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
        for file_path in distro_summary.all_paths:
            path_lower_to_raw[file_path.lower()].append(file_path)

        duplicates_list: List[str] = []
        for filepaths in path_lower_to_raw.values():
            if len(filepaths) > 1:
                duplicates_list += filepaths

        if duplicates_list:
            duplicates_str = ",".join(sorted(duplicates_list))
            msg = (
                f"[{self.check_name}] Found files which differ only by case. "
                f"Files: {duplicates_str}"
            )
            out.append(msg)
        return out


class _NonAsciiCharacterCheck(_CheckProtocol):
    check_name = "path-contains-non-ascii-characters"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for file_path in distro_summary.all_paths:
            if not file_path.isascii():
                ascii_converted_str = file_path.encode("ascii", "replace").decode(
                    "ascii"
                )
                msg = (
                    f"[{self.check_name}] Found file path containing non-ASCII characters: "
                    f"'{ascii_converted_str}'"
                )
                out.append(msg)
        return out


class _MixedFileExtensionCheck(_CheckProtocol):
    check_name = "mixed-file-extensions"

    file_ext_groups = (
        {".cc", ".CC", ".cpp", ".CPP"},
        {".htm", ".HTM", ".html", ".HTML"},
        {".jpg", ".JPG", ".jpeg", ".JPEG"},
        {".jsonl", ".JSONL", ".ndjson", ".NDJSON"},
        {".txt", ".TXT", ".text", ".TEXT"},
        {".yaml", ".YAML", ".yml", ".YML"},
    )

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        file_extensions_in_distro = set(distro_summary.files_by_extension.keys())
        for file_ext_group in self.file_ext_groups:
            extensions_found = file_ext_group.intersection(file_extensions_in_distro)
            if len(extensions_found) >= 2:
                count_str = ", ".join(
                    f"{ext} ({distro_summary.count_by_file_extension[ext]})"
                    for ext in sorted(extensions_found)
                )
                msg = (
                    f"[{self.check_name}] Found a mix of file extensions for "
                    f"the same file type: {count_str}"
                )
                out.append(msg)
        return out


class _PathTooLongCheck(_CheckProtocol):
    check_name = "path-too-long"

    def __init__(self, *, max_path_length: int):
        self.max_path_length = max_path_length

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        bad_paths = [
            p for p in distro_summary.all_paths if len(p) > self.max_path_length
        ]
        for file_path in bad_paths:
            msg = (
                f"[{self.check_name}] Path too long ({len(file_path)} > {self.max_path_length}): "
                f"'{file_path}'"
            )
            out.append(msg)
        return out


class _SpacesInPathCheck(_CheckProtocol):
    check_name = "path-contains-spaces"

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for file_path in distro_summary.all_paths:
            if file_path != file_path.replace(" ", ""):
                msg = f"[{self.check_name}] Found path with spaces: '{file_path}'"
                out.append(msg)
        return out


class _ExpectedFilesCheck(_CheckProtocol):
    check_name = "expected-files"

    def __init__(
        self,
        *,
        directory_patterns: Sequence[str],
        file_patterns: Sequence[str],
    ):
        self.directory_patterns = [
            d for d in directory_patterns if not d.startswith("!")
        ]
        self.file_patterns = [f for f in file_patterns if not f.startswith("!")]

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for pattern in self.file_patterns:
            found_any = False
            for file_path in distro_summary.file_paths:
                if fnmatchcase(file_path, pattern):
                    found_any = True
                    break

            if not found_any:
                msg = f"[{self.check_name}] Did not find any files matching pattern '{pattern}'."
                out.append(msg)

        for pattern in self.directory_patterns:
            found_any = False
            for directory_path in distro_summary.directory_paths:
                # NOTE: some archive formats have a trailing "/" on directory names,
                #       some do not
                if fnmatchcase(directory_path, pattern) or fnmatchcase(
                    directory_path, pattern + "/"
                ):
                    found_any = True
                    break
            if not found_any:
                msg = f"[{self.check_name}] Did not find any directories matching pattern '{pattern}'."
                out.append(msg)
        return out


class _UnexpectedFilesCheck(_CheckProtocol):
    check_name = "unexpected-files"

    def __init__(
        self,
        *,
        directory_patterns: Sequence[str],
        file_patterns: Sequence[str],
    ):
        self.directory_patterns = [
            d[1:] for d in directory_patterns if d.startswith("!")
        ]
        self.file_patterns = [f[1:] for f in file_patterns if f.startswith("!")]

    def __call__(self, distro_summary: _DistributionSummary) -> List[str]:
        out: List[str] = []
        for file_path in distro_summary.file_paths:
            for pattern in self.file_patterns:
                if fnmatchcase(file_path, pattern):
                    msg = f"[{self.check_name}] Found unexpected file '{file_path}'."
                    out.append(msg)

        for directory_path in distro_summary.directory_paths:
            for pattern in self.directory_patterns:
                # NOTE: some archive formats have a trailing "/" on directory names,
                #       some do not
                if fnmatchcase(directory_path, pattern) or fnmatchcase(
                    directory_path, pattern + "/"
                ):
                    msg = f"[{self.check_name}] Found unexpected directory '{directory_path}'."
                    out.append(msg)
        return out
