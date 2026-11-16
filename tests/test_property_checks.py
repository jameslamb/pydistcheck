"""Property-based tests for pydistcheck's pure checks and size helpers.

Distributions are data this project doesn't control, so these tests generate
random file names, paths, and sizes to look for edge cases the example-based
integration tests miss (see GH issue #108).
"""

from __future__ import annotations

from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from pydistcheck._checks import (
    _DistroTooLargeCompressedCheck,
    _DistroTooLargeUnCompressedCheck,
    _FileCountCheck,
    _FilesOnlyDifferByCaseCheck,
    _MixedFileExtensionCheck,
    _NonAsciiCharacterCheck,
    _PathTooLongCheck,
    _SpacesInPathCheck,
)
from pydistcheck._distribution_summary import _DistributionSummary
from pydistcheck._file_utils import (
    _ArchiveFormat,
    _DirectoryInfo,
    _FileFormat,
    _FileInfo,
)
from pydistcheck._utils import _FileSize

# Spaces, non-ASCII, and mixed case are all intentional here: those are exactly
# the inputs the path checks exist to flag. Path separators and NUL are left
# out so generated strings remain plausible archive member names.
_PATH_SEGMENTS = st.text(
    alphabet=st.characters(
        blacklist_characters=("\x00", "/", "\\"),
        blacklist_categories=("Cs",),
    ),
    min_size=1,
    max_size=60,
)

_SIZES = st.integers(min_value=0, max_value=10**9)


def _summary(
    file_paths: list[str],
    *,
    compressed_size_bytes: int = 0,
    directory_paths: list[str] | None = None,
    file_sizes: list[int] | None = None,
) -> _DistributionSummary:
    files = [
        _FileInfo(
            name=path,
            file_format=_FileFormat.OTHER,
            file_extension=Path(path).suffix or "no-extension",
            is_compiled=False,
            uncompressed_size_bytes=(
                file_sizes[index] if file_sizes else len(path.encode("utf-8"))
            ),
        )
        for index, path in enumerate(file_paths)
    ]
    return _DistributionSummary(
        archive_format=_ArchiveFormat.ZIP,
        compressed_size_bytes=compressed_size_bytes,
        directories=[_DirectoryInfo(name=d) for d in directory_paths or []],
        files=files,
        original_file="example.zip",
    )


@given(num_bytes=st.integers(min_value=0, max_value=1024))
def test_file_size_from_string_of_bytes_is_exact(num_bytes: int) -> None:
    assert _FileSize.from_string(f"{num_bytes}B").total_size_bytes == num_bytes


@given(
    a=st.integers(min_value=0, max_value=10**9),
    b=st.integers(min_value=0, max_value=10**9),
)
def test_file_size_comparisons_follow_total_bytes(a: int, b: int) -> None:
    left = _FileSize(num=a, unit_str="B")
    right = _FileSize(num=b, unit_str="B")
    assert (left < right) == (a < b)
    assert (left <= right) == (a <= b)
    assert (left > right) == (a > b)
    assert (left >= right) == (a >= b)
    assert (left == right) == (a == b)


@given(paths=st.lists(_PATH_SEGMENTS, max_size=20))
def test_spaces_in_path_flags_exactly_paths_with_spaces(paths: list[str]) -> None:
    messages = _SpacesInPathCheck()(_summary(paths))
    expected = [p for p in paths if " " in p]
    assert len(messages) == len(expected)
    for path in expected:
        assert any(path in message for message in messages)


@given(paths=st.lists(_PATH_SEGMENTS, max_size=20))
def test_non_ascii_check_flags_exactly_non_ascii_paths(paths: list[str]) -> None:
    messages = _NonAsciiCharacterCheck()(_summary(paths))
    expected = [p for p in paths if not p.isascii()]
    # The message replaces non-ASCII characters with '?', so only count them.
    assert len(messages) == len(expected)


@given(
    paths=st.lists(_PATH_SEGMENTS, max_size=20),
    limit=st.integers(min_value=0, max_value=100),
)
def test_path_too_long_flags_exactly_overlong_paths(
    paths: list[str], limit: int
) -> None:
    messages = _PathTooLongCheck(max_path_length=limit)(_summary(paths))
    assert len(messages) == sum(len(p) > limit for p in paths)


@given(paths=st.lists(_PATH_SEGMENTS, max_size=20))
def test_files_only_differ_by_case_detects_case_collisions(
    paths: list[str],
) -> None:
    messages = _FilesOnlyDifferByCaseCheck()(_summary(paths))
    groups: dict[str, list[str]] = {}
    for path in paths:
        groups.setdefault(path.lower(), []).append(path)
    duplicates = [p for group in groups.values() if len(group) > 1 for p in group]
    assert bool(messages) == bool(duplicates)
    for path in duplicates:
        assert any(path in message for message in messages)


@given(
    num_files=st.integers(min_value=0, max_value=50),
    limit=st.integers(min_value=0, max_value=50),
)
def test_file_count_check_reports_over_limit(num_files: int, limit: int) -> None:
    paths = [f"file_{i}.py" for i in range(num_files)]
    messages = _FileCountCheck(max_allowed_files=limit)(_summary(paths))
    assert len(messages) == (1 if num_files > limit else 0)


@given(compressed=_SIZES, limit=_SIZES)
def test_compressed_size_check_reports_over_limit(compressed: int, limit: int) -> None:
    check = _DistroTooLargeCompressedCheck(
        max_allowed_size_bytes=limit,
        output_file_size_precision=2,
        output_file_size_unit="B",
    )
    messages = check(_summary([], compressed_size_bytes=compressed))
    assert len(messages) == (1 if compressed > limit else 0)


@given(sizes=st.lists(_SIZES, max_size=10), limit=_SIZES)
def test_uncompressed_size_check_reports_over_limit(
    sizes: list[int], limit: int
) -> None:
    paths = [f"file_{i}.py" for i in range(len(sizes))]
    check = _DistroTooLargeUnCompressedCheck(
        max_allowed_size_bytes=limit,
        output_file_size_precision=2,
        output_file_size_unit="B",
    )
    messages = check(_summary(paths, file_sizes=sizes))
    assert len(messages) == (1 if sum(sizes) > limit else 0)


@given(paths=st.lists(_PATH_SEGMENTS, max_size=15))
def test_pure_checks_return_tagged_string_lists(paths: list[str]) -> None:
    summary = _summary(paths)
    checks = [
        _DistroTooLargeCompressedCheck(
            max_allowed_size_bytes=100,
            output_file_size_precision=2,
            output_file_size_unit="B",
        ),
        _DistroTooLargeUnCompressedCheck(
            max_allowed_size_bytes=100,
            output_file_size_precision=2,
            output_file_size_unit="B",
        ),
        _FileCountCheck(max_allowed_files=5),
        _FilesOnlyDifferByCaseCheck(),
        _MixedFileExtensionCheck(),
        _NonAsciiCharacterCheck(),
        _PathTooLongCheck(max_path_length=10),
        _SpacesInPathCheck(),
    ]
    for check in checks:
        result = check(summary)
        assert isinstance(result, list)
        assert all(
            isinstance(message, str) and message.startswith(f"[{check.check_name}]")
            for message in result
        )
