import os
import re
import pytest

from typing import List
from click.testing import CliRunner, Result
from pydistcheck.cli import check

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def _assert_log_matches_pattern(result: Result, pattern: str) -> None:
    log_lines = result.output.split("\n")
    match_results = [bool(re.search(pattern, l)) for l in log_lines]
    num_matches_found = sum(match_results)
    msg = f"Expected to find 1 instance of '{pattern}' in logs, found {num_matches_found} in {log_lines}."
    assert num_matches_found == 1, msg


@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_runs_without_error(distro_file):
    runner = CliRunner()
    result = runner.invoke(check, [os.path.join(TEST_DATA_DIR, distro_file)])
    assert result.exit_code == 0


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
        r"^1\. \[distro\-too\-large\-compressed\] Compressed size [0-9]+\.[0-9]+K is larger than the allowed size \([0-9]+\.[0-9]+[BKMG]\)\.$",
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
        r"^1\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+K is larger than the allowed size \([0-9]+\.[0-9]+[BKMG]\)\.$",
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")
