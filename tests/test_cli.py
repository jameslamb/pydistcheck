import os
import re

import pytest
from click.testing import CliRunner, Result

from pydistcheck.cli import check

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _assert_log_matches_pattern(result: Result, pattern: str, num_times: int = 1) -> None:
    log_lines = result.output.split("\n")
    match_results = [bool(re.search(pattern, log_line)) for log_line in log_lines]
    num_matches_found = sum(match_results)
    msg = (
        f"Expected to find 1 instance of '{pattern}' in logs, "
        f"found {num_matches_found} in {log_lines}."
    )
    assert num_matches_found == num_times, msg


@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_runs_without_error(distro_file):
    runner = CliRunner()
    result = runner.invoke(check, [os.path.join(TEST_DATA_DIR, distro_file)])
    assert result.exit_code == 0


def test_check_fails_with_informative_error_if_file_doesnt_exist():
    runner = CliRunner()
    result = runner.invoke(check, ["some-garbage.exe"])
    assert result.exit_code > 0
    _assert_log_matches_pattern(result, r"Path 'some\-garbage\.exe' does not exist\.$")


def test_check_runs_for_all_files_before_exiting():
    runner = CliRunner()
    result = runner.invoke(
        check,
        [
            "--max-allowed-size-compressed=5B",
            os.path.join(TEST_DATA_DIR, "base-package.tar.gz"),
            os.path.join(TEST_DATA_DIR, "base-package.zip"),
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^1\. \[distro\-too\-large\-compressed\] Compressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \(5\.0B\)\.$"
        ),
        num_times=2,
    )
    _assert_log_matches_pattern(
        result=result, pattern="errors found while checking\\: 1", num_times=2
    )


@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_respects_max_allowed_files(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check, [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-files=1"]
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result, r"^1\. \[too\-many\-files\] Found 3 files\. Only 1 allowed\.$"
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize(
    "size_str",
    [
        "1K",
        "3.999K",
        "0.0002M",
        "0.00000008G",
        "708B",
    ],
)
@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_respects_max_allowed_size_compressed(size_str, distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file), f"--max-allowed-size-compressed={size_str}"],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-compressed\] Compressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \([0-9]+\.[0-9]+[BKMG]\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize(
    "size_str",
    [
        "1K",
        "3.999K",
        "0.0002M",
        "0.00000008G",
        "708B",
    ],
)
@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_respects_max_allowed_size_uncompressed(size_str, distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file), f"--max-allowed-size-uncompressed={size_str}"],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \([0-9]+\.[0-9]+[BKMG]\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize("distro_file", ["problematic-package.tar.gz", "problematic-package.zip"])
def test_cli_raises_exactly_the_expected_number_of_errors_for_the_probllematic_package(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: 4$")


@pytest.mark.parametrize("distro_file", ["problematic-package.tar.gz", "problematic-package.zip"])
def test_files_only_differ_by_case_works(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^1\. \[files\-only\-differ\-by\-case\] Found files which differ only by case\. "
            r"Such files are not portable, since some filesystems are case-insensitive\. "
            r"Files\: tmp/problematic-package/question\.PY,tmp/problematic-package/question\.py"
            r",tmp/problematic-package/Question\.py"
        ),
    )
    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


@pytest.mark.parametrize("distro_file", ["problematic-package.tar.gz", "problematic-package.zip"])
def test_path_contains_spaces_works(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # should report a file with spaces in a directory without spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^2\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: 'tmp/problematic\-package/beep boop\.ini"
        ),
    )

    # should report a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^3\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: 'tmp/problematic\-package/bad code[/]*"
        ),
    )

    # should report a file without spaces inside a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^4\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: 'tmp/problematic\-package/bad code/ship\-it\.py"
        ),
    )

    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


# --------------------- #
# pydistcheck --inspect #
# --------------------- #


@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_inspect_runs_before_checks(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check, ["--inspect", "--max-allowed-files=1", os.path.join(TEST_DATA_DIR, distro_file)]
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result, r"^1\. \[too\-many\-files\] Found 3 files\. Only 1 allowed\.$"
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")
    _assert_log_matches_pattern(result, r"^size by extension$")
