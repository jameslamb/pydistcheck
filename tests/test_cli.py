import os
import re
from sys import platform

import pytest
from click.testing import CliRunner, Result

from pydistcheck.cli import check

BASE_PACKAGES = ["base-package-0.1.0.tar.gz", "base-package-0.1.0.zip"]
PROBLEMATIC_PACKAGES = ["problematic-package-0.1.0.tar.gz", "problematic-package-0.1.0.zip"]
MACOS_SUFFIX = "macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl"
MANYLINUX_SUFFIX = "manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl"
BASE_WHEELS = [
    f"baseballmetrics-0.1.0-py3-none-{MACOS_SUFFIX}",
    f"baseballmetrics-0.1.0-py3-none-{MANYLINUX_SUFFIX}",
]
WHEELS_WITH_DEBUG_SYMBOLS = [
    f"debug-baseballmetrics-0.1.0-py3-none-{MACOS_SUFFIX}",
    f"debug-baseballmetrics-py3-none-{MANYLINUX_SUFFIX}",
]
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


@pytest.mark.parametrize("distro_file", BASE_PACKAGES + BASE_WHEELS)
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
            os.path.join(TEST_DATA_DIR, "base-package-0.1.0.tar.gz"),
            os.path.join(TEST_DATA_DIR, "base-package-0.1.0.zip"),
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


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_ignore_with_one_check(distro_file):
    runner = CliRunner()

    # fails when running all checks
    result = runner.invoke(
        check, [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-files=1"]
    )
    assert result.exit_code == 1

    # fails with --ignore if the failing check isn't mentioned in --ignore
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=path-contains-spaces",
            "--max-allowed-files=1",
        ],
    )
    assert result.exit_code == 1

    # succeeds if the failing check is mentioned in --ignore
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=too-many-files",
            "--max-allowed-files=1",
        ],
    )
    assert result.exit_code == 0
    _assert_log_matches_pattern(result, "errors found while checking\\: 0")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_ignore_with_multiple_checks(distro_file):
    runner = CliRunner()

    # fails when running all checks
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--max-allowed-files=1",
            "--max-allowed-size-compressed=1B",
        ],
    )
    assert result.exit_code == 1

    # fails with --ignore if all of the failing checks aren't mentioned in --ignore
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=path-contains-spaces,too-many-files",
            "--max-allowed-files=1",
            "--max-allowed-size-compressed=1B",
        ],
    )
    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-compressed\] Compressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \(1\.0B\)\.$"
        ),
    )
    assert result.exit_code == 1

    # succeeds if the failing checks are mentioned in --ignore
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=too-many-files,distro-too-large-compressed",
            "--max-allowed-files=1",
        ],
    )
    assert result.exit_code == 0
    _assert_log_matches_pattern(result, "errors found while checking\\: 0")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_fails_with_expected_error_if_one_check_is_unrecognized(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file), "--ignore=too-many-files,random-nonsense"],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"ERROR\: found the following unrecognized checks passed via '\-\-ignore'\: "
            r"random\-nonsense"
        ),
    )


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_fails_with_expected_error_if_multiple_checks_are_unrecognized(distro_file):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=garbage,too-many-files,random-nonsense,other-trash",
        ],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"ERROR\: found the following unrecognized checks passed via '\-\-ignore'\: "
            r"garbage,other\-trash,random\-nonsense"
        ),
    )


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_max_allowed_files(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check, [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-files=1"]
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result, r"^1\. \[too\-many\-files\] Found 11 files\. Only 1 allowed\.$"
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
@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
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
@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
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


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_prefers_pyproject_toml_to_defaults(distro_file, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("pyproject.toml", "w") as f:
            f.write("[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '7B'\n")
        result = runner.invoke(
            check,
            [os.path.join(TEST_DATA_DIR, distro_file)],
        )

    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \(7\.0B\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_handles_ignore_list_in_pyproject_toml_correctly(distro_file, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(
            check,
            [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-files=1"],
        )
        assert result.exit_code == 1
        _assert_log_matches_pattern(
            result, r"^1\. \[too\-many\-files\] Found [0-9]+ files\. Only 1 allowed\.$"
        )
        with open("pyproject.toml", "w") as f:
            f.write(
                "[tool.pylint]\n[tool.pydistcheck]\n"
                "ignore = [\n'too-many-files', 'path-contains-non-ascii-characters'\n]\n"
            )
        result = runner.invoke(
            check,
            [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-files=1"],
        )
        assert result.exit_code == 0
        _assert_log_matches_pattern(result, "errors found while checking\\: 0")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_prefers_keyword_args_to_pyrpoject_toml_and_defaults(distro_file, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("pyproject.toml", "w") as f:
            f.write("[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '7B'\n")
        result = runner.invoke(
            check,
            [os.path.join(TEST_DATA_DIR, distro_file), "--max-allowed-size-uncompressed=123B"],
        )

    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \(0\.1K\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_cli_raises_exactly_the_expected_number_of_errors_for_the_problematic_package(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: 10$")


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
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
            r"Files\: problematic\-package\-0\.1\.0/problematic_package/Question\.py"
            r",problematic\-package\-0\.1\.0/problematic_package/question\.PY"
            r",problematic\-package\-0\.1\.0/problematic_package/question\.py"
        ),
    )
    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
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
            r"^3\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: 'problematic\-package\-0\.1\.0/beep boop\.ini"
        ),
    )

    # should report a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^4\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code[/]*"
        ),
    )

    # should report a file without spaces inside a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^5\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code/__init__\.py"
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^6\. \[path\-contains\-spaces\] File paths with spaces are not portable\. "
            r"Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code/ship\-it\.py"
        ),
    )

    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_path_contains_non_ascii_characters_works(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # NOTE: matching a variable number of '?' because zip and tar (and even different
    #       implementations of those) encode non-ASCII characters in paths differently
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^2\. \[path\-contains\-non\-ascii\-characters\] Found file path containing non-ASCII "
            r"characters\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/\?+veryone-loves-python\.py'"
        ),
    )

    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_unexpected_files_check_works(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # directory
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^7\. \[unexpected\-files\] Found unexpected directory "
            r"'problematic\-package\-0\.1\.0/\.git[/]{0,1}'\."
        ),
    )

    # root-level files
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^8\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/\.gitignore'\."
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^9\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/\.hadolint\.yaml'\."
        ),
    )

    # nested files
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^10\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/problematic_package/\.gitignore'\."
        ),
    )

    _assert_log_matches_pattern(result=result, pattern=r"errors found while checking\: [0-9]{1}")


@pytest.mark.parametrize("distro_file", WHEELS_WITH_DEBUG_SYMBOLS)
def test_debug_symbols_check_works(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1, result.output
    if "macosx" in distro_file:
        if platform.startswith("cygwin") or platform.startswith("win"):
            debug_cmd = r"'llvm\-nm \-\-debug\-syms \"lib/lib_baseballmetrics\.dylib\"'\."
        else:
            # dsymutil works on both macOS and Linux
            debug_cmd = r"'dsymutil \-s \"lib/lib_baseballmetrics\.dylib\"'\."
    else:
        debug_cmd = r"'objdump \-\-all\-headers \"lib/lib_baseballmetrics\.so\"'\."

    expected_msg = (
        r"^1\. \[compiled\-objects\-have\-debug\-symbols\] "
        r"Found compiled object containing debug symbols\. "
        r"For details, extract the distribution contents and run "
    )
    expected_msg += debug_cmd
    _assert_log_matches_pattern(result=result, pattern=expected_msg)


# --------------------- #
# pydistcheck --inspect #
# --------------------- #


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_inspect_runs_before_checks(distro_file):
    runner = CliRunner()
    result = runner.invoke(
        check, ["--inspect", "--max-allowed-files=1", os.path.join(TEST_DATA_DIR, distro_file)]
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result, r"^1\. \[too\-many\-files\] Found 11 files\. Only 1 allowed\.$"
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")
    _assert_log_matches_pattern(result, r"^size by extension$")
