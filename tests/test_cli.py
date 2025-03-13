import os
import re
from sys import platform
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner, Result

import pydistcheck.cli  # noqa: F401
from pydistcheck.cli import check

BASE_PACKAGES = [
    "base-package-0.1.0.tar.gz",
    "base-package-0.1.0.zip",
]
PROBLEMATIC_PACKAGES = [
    "problematic-package-0.1.0.tar.gz",
    "problematic-package-0.1.0.zip",
]
MACOS_SUFFIX = "macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl"
MANYLINUX_SUFFIX = "manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl"
BASEBALL_CONDA_PACKAGES = [
    "osx-64-baseballmetrics-0.1.0-0.conda",
    "osx-64-baseballmetrics-0.1.0-0.tar.bz2",
]
BASEBALL_WHEELS = [
    f"baseballmetrics-0.1.0-py3-none-{MACOS_SUFFIX}",
    f"baseballmetrics-0.1.0-py3-none-{MANYLINUX_SUFFIX}",
]
BASEBALL_PACKAGES = BASEBALL_CONDA_PACKAGES + BASEBALL_WHEELS
# NOTE: .bz2 and .tar.gz packages here are just unzipped
#       and re-tarred Python wheels... to avoid pydistcheck
#       implicitly assuming that, for example, '*.tar.gz' must
#       be an sdist and therefore not have compiled objects
PACKAGES_WITH_DEBUG_SYMBOLS = [
    "debug-baseballmetrics-0.1.0-macosx-wheel.tar.bz2",
    "debug-baseballmetrics-0.1.0-macosx-wheel.tar.gz",
    f"debug-baseballmetrics-0.1.0-py3-none-{MACOS_SUFFIX}",
    f"debug-baseballmetrics-py3-none-{MANYLINUX_SUFFIX}",
    "osx-64-debug-baseballmetrics-0.1.0-0.conda",
    "osx-64-debug-baseballmetrics-0.1.0-0.tar.bz2",
]
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# see https://github.com/jameslamb/pydistcheck/issues/206
NUMPY_WIN_DEBUG_WHL = "numpy-1.26.3-cp310-cp310-win_amd64.whl"
if os.path.isfile(os.path.join(TEST_DATA_DIR, NUMPY_WIN_DEBUG_WHL)):
    PACKAGES_WITH_DEBUG_SYMBOLS.append(NUMPY_WIN_DEBUG_WHL)


def _assert_log_matches_pattern(
    result: Result, pattern: str, num_times: int = 1
) -> None:
    log_lines = result.output.split("\n")
    match_results = [bool(re.search(pattern, log_line)) for log_line in log_lines]
    num_matches_found = sum(match_results)
    msg = (
        f"Expected to find 1 instance of '{pattern}' in logs, "
        f"found {num_matches_found} in {log_lines}."
    )
    assert num_matches_found == num_times, msg


def _mock_check_num_calls(mock_check: MagicMock) -> int:
    """returns count of times the __call__() method of a mocked check class instance was called"""
    return sum(
        1
        for mc in mock_check.method_calls
        if str(mc).startswith("call()(distro_summary=")
    )


@pytest.mark.parametrize("distro_file", BASE_PACKAGES + BASEBALL_PACKAGES)
def test_check_runs_without_error(distro_file):
    result = CliRunner().invoke(check, [os.path.join(TEST_DATA_DIR, distro_file)])
    assert result.exit_code == 0


def test_version_flag_works():
    result = CliRunner().invoke(
        check,
        [
            "--version",
        ],
    )
    assert result.exit_code == 0

    _assert_log_matches_pattern(
        result=result,
        pattern=(r"^pydistcheck [0-9]{1}\.[0-9]{1,2}\.[0-9]{1,2}\.*[0-9]*$"),
        num_times=1,
    )


def test_check_fails_with_informative_error_if_file_doesnt_exist():
    result = CliRunner().invoke(check, ["some-garbage.exe"])
    # NOTE: this exit code comes from 'click'
    assert result.exit_code >= 1
    _assert_log_matches_pattern(result, r"Path 'some\-garbage\.exe' does not exist\.$")


def test_check_runs_for_all_files_before_exiting():
    result = CliRunner().invoke(
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


@pytest.mark.parametrize("flags", ([], ["--inspect"]))
def test_check_fails_with_informative_error_if_file_is_an_unrecognized_format(flags):
    result = CliRunner().invoke(check, [__file__, *flags])
    assert result.exit_code == 2
    _assert_log_matches_pattern(
        result, r"error.*File '.*' does not appear to be a Python package distribution"
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
            "--ignore=path-contains-spaces",
            "--ignore=too-many-files",
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
            "--ignore=distro-too-large-compressed",
            "--ignore=too-many-files",
            "--max-allowed-files=1",
        ],
    )
    assert result.exit_code == 0
    _assert_log_matches_pattern(result, "errors found while checking\\: 0")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_fails_with_expected_error_if_one_check_in_ignore_is_unrecognized(
    distro_file,
):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=random-nonsense",
            "--ignore=too-many-files",
        ],
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
def test_check_fails_with_expected_error_if_multiple_checks_in_ignore_are_unrecognized(
    distro_file,
):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=garbage",
            "--ignore=other-trash",
            "--ignore=random-nonsense",
            "--ignore=too-many-files",
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


@patch("pydistcheck.cli._SpacesInPathCheck", autospec=True)
@patch("pydistcheck.cli._FileCountCheck", autospec=True)
@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_select_with_one_check(
    mock_path_contains_spaces, mock_too_many_files, distro_file
):
    # ensure this attribute is actually set, as it's used for filtering (the class attribute
    # is lost somewhere in all this mocking and patching)
    mock_path_contains_spaces.return_value.check_name = "path-contains-spaces"
    mock_too_many_files.return_value.check_name = "too-many-files"

    # initialize the click testing class
    runner = CliRunner()

    # by default, all checks should be selected and run once
    result = runner.invoke(check, [os.path.join(TEST_DATA_DIR, distro_file)])
    assert result.exit_code == 0
    assert _mock_check_num_calls(mock_path_contains_spaces) == 1
    assert _mock_check_num_calls(mock_too_many_files) == 1
    mock_path_contains_spaces.reset_mock()
    mock_too_many_files.reset_mock()

    # passing '--select' switches pydistcheck to opt-in mode... no other checks should run
    # except those mentioned in '--select'
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--select=too-many-files",
        ],
    )
    assert result.exit_code == 0
    _assert_log_matches_pattern(result, "errors found while checking\\: 0")
    assert _mock_check_num_calls(mock_path_contains_spaces) == 0
    assert _mock_check_num_calls(mock_too_many_files) == 1
    mock_path_contains_spaces.reset_mock()
    mock_too_many_files.reset_mock()

    # if a check is present in '--select', it doesn't matter that it's present in '--ignore'
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--ignore=too-many-files",
            "--select=too-many-files",
        ],
    )
    assert result.exit_code == 0
    assert _mock_check_num_calls(mock_path_contains_spaces) == 0
    assert _mock_check_num_calls(mock_too_many_files) == 1
    mock_path_contains_spaces.reset_mock()
    mock_too_many_files.reset_mock()


@patch("pydistcheck.cli._PathTooLongCheck", autospec=True)
@patch("pydistcheck.cli._SpacesInPathCheck", autospec=True)
@patch("pydistcheck.cli._FileCountCheck", autospec=True)
@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_select_with_multiple_checks(
    mock_path_too_long, mock_path_contains_spaces, mock_too_many_files, distro_file
):
    # ensure this attribute is actually set, as it's used for filtering (the class attribute
    # is lost somewhere in all this mocking and patching)
    mock_path_too_long.return_value.check_name = "path-too-long"
    mock_path_contains_spaces.return_value.check_name = "path-contains-spaces"
    mock_too_many_files.return_value.check_name = "too-many-files"

    # initialize the click testing class
    runner = CliRunner()

    # by default, all checks should be selected and run once
    result = runner.invoke(check, [os.path.join(TEST_DATA_DIR, distro_file)])
    assert result.exit_code == 0
    assert _mock_check_num_calls(mock_path_too_long) == 1
    assert _mock_check_num_calls(mock_path_contains_spaces) == 1
    assert _mock_check_num_calls(mock_too_many_files) == 1
    mock_path_too_long.reset_mock()
    mock_path_contains_spaces.reset_mock()
    mock_too_many_files.reset_mock()

    # passing '--select' switches pydistcheck to opt-in mode... no other checks should run
    # except those mentioned in '--select'
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--select=too-many-files",
            "--select=path-too-long",
        ],
    )
    assert result.exit_code == 0
    _assert_log_matches_pattern(result, "errors found while checking\\: 0")
    assert _mock_check_num_calls(mock_path_too_long) == 1
    assert _mock_check_num_calls(mock_path_contains_spaces) == 0
    assert _mock_check_num_calls(mock_too_many_files) == 1
    mock_path_too_long.reset_mock()
    mock_path_contains_spaces.reset_mock()
    mock_too_many_files.reset_mock()


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_fails_with_expected_error_if_one_check_in_select_is_unrecognized(
    distro_file,
):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--select=random-nonsense",
            "--ignore=too-many-files",
        ],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"ERROR\: found the following unrecognized checks passed via '\-\-select'\: "
            r"random\-nonsense"
        ),
    )


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_fails_with_expected_error_if_multiple_checks_in_select_are_unrecognized(
    distro_file,
):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--select=garbage",
            "--select=other-trash",
            "--select=random-nonsense",
            "--select=too-many-files",
        ],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"ERROR\: found the following unrecognized checks passed via '\-\-select'\: "
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
        "0.005KB",
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
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            f"--max-allowed-size-compressed={size_str}",
        ],
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


@pytest.mark.parametrize("unit_str", ["B", "K", "KB", "Mi", "GB", "Gi"])
def test_check_error_messages_supports_output_file_size_unit(unit_str):
    runner = CliRunner()
    result = runner.invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, BASE_PACKAGES[1]),
            "--max-allowed-size-compressed=1B",
            "--max-allowed-size-uncompressed=1B",
            f"--output-file-size-unit={unit_str}",
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result,
        (
            rf"^1\. \[distro\-too\-large\-compressed\] Compressed size [0-9]+\.[0-9]+{unit_str} is "
            rf"larger than the allowed size \([0-9]+\.[0-9]+{unit_str}\)\.$"
        ),
    )
    _assert_log_matches_pattern(
        result,
        (
            rf"^2\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+{unit_str} is "
            rf"larger than the allowed size \([0-9]+\.[0-9]+{unit_str}\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 2")


def test_check_error_messages_supports_output_file_size_precision():
    # default precision
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, BASE_PACKAGES[1]),
            "--max-allowed-size-compressed=256B",
            "--max-allowed-size-uncompressed=256B",
            "--output-file-size-unit=MB",
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-compressed\] Compressed size 0\.007MB is "
            r"larger than the allowed size \(0\.0MB\)\.$"
        ),
    )
    _assert_log_matches_pattern(
        result,
        (
            r"^2\. \[distro\-too\-large\-uncompressed\] Uncompressed size 0\.012MB is "
            r"larger than the allowed size \(0\.0MB\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 2")

    # precision 5
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, BASE_PACKAGES[1]),
            "--max-allowed-size-compressed=256B",
            "--max-allowed-size-uncompressed=256B",
            "--output-file-size-precision=5",
            "--output-file-size-unit=MB",
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-compressed\] Compressed size 0\.00681MB is "
            r"larger than the allowed size \(0\.00026MB\)\.$"
        ),
    )
    _assert_log_matches_pattern(
        result,
        (
            r"^2\. \[distro\-too\-large\-uncompressed\] Uncompressed size 0\.01233MB is "
            r"larger than the allowed size \(0\.00026MB\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 2")


@pytest.mark.parametrize(
    "size_str",
    [
        "1",
        "K",
        "1-KB",
        "GB1",
        "1G-B",
    ],
)
@pytest.mark.parametrize(
    "cli_arg",
    [
        "--max-allowed-size-compressed",
        "--max-allowed-size-uncompressed",
    ],
)
def test_check_raises_informative_error_for_malformed_file_size_config(
    cli_arg, size_str
):
    with pytest.raises(
        ValueError, match=rf"Could not parse '{size_str}' as a file size"
    ):
        CliRunner().invoke(
            check,
            [
                os.path.join(TEST_DATA_DIR, BASE_PACKAGES[0]),
                f"{cli_arg}={size_str}",
            ],
            catch_exceptions=False,
        )


@pytest.mark.parametrize(
    "size_str",
    [
        "1K",
        "3.999K",
        "0.005KB",
        "0.0002M",
        "0.00000008G",
        "708B",
    ],
)
@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_respects_max_allowed_size_uncompressed(size_str, distro_file):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            f"--max-allowed-size-uncompressed={size_str}",
        ],
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
            f.write(
                "[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '7B'\n"
            )
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
def test_check_prefers_keyword_args_to_pyproject_toml_and_defaults(
    distro_file, tmp_path
):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("pyproject.toml", "w") as f:
            f.write(
                "[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '7B'\n"
            )
        result = runner.invoke(
            check,
            [
                os.path.join(TEST_DATA_DIR, distro_file),
                "--max-allowed-size-uncompressed=123B",
            ],
        )

    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result,
        (
            r"^1\. \[distro\-too\-large\-uncompressed\] Uncompressed size [0-9]+\.[0-9]+K is "
            r"larger than the allowed size \(0\.12K\)\.$"
        ),
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")


@pytest.mark.parametrize("distro_file", BASE_PACKAGES)
def test_check_prefers_custom_toml_file_to_root_pyproject_toml(distro_file, tmp_path):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        with open("pyproject.toml", "w") as f:
            f.write(
                "[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '10GB'\n"
            )
        other_dir = os.path.join(tmp_path, "cool-files")
        other_config = os.path.join(other_dir, "stuff.toml")
        os.mkdir(other_dir)
        with open(other_config, "w") as f:
            f.write(
                "[tool.pylint]\n[tool.pydistcheck]\nmax_allowed_size_uncompressed = '7B'\n"
            )
        result = runner.invoke(
            check,
            [os.path.join(TEST_DATA_DIR, distro_file), f"--config={other_config}"],
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


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_files_only_differ_by_case_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^1\. \[files\-only\-differ\-by\-case\] Found files which differ only by case\. "
            r"Files\: problematic\-package\-0\.1\.0/problematic_package/Question\.py"
            r",problematic\-package\-0\.1\.0/problematic_package/question\.PY"
            r",problematic\-package\-0\.1\.0/problematic_package/question\.py"
        ),
    )
    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_mixed_file_extension_use_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^2\. \[mixed\-file\-extensions\] Found a mix of file extensions for the "
            r"same file type\: \.NDJSON \(1\), \.jsonl \(1\), \.ndjson \(1\)"
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^3\. \[mixed\-file\-extensions\] Found a mix of file extensions for the "
            r"same file type\: \.yaml \(2\), \.yml \(1\)"
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_path_contains_non_ascii_characters_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # NOTE: matching a variable number of '?' because zip and tar (and even different
    #       implementations of those) encode non-ASCII characters in paths differently
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^4\. \[path\-contains\-non\-ascii\-characters\] Found file path containing non-ASCII "
            r"characters\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/\?+veryone-loves-python\.py'"
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_path_contains_spaces_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # should report a file with spaces in a directory without spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^5\. \[path\-contains\-spaces\] "
            r"Found path with spaces\: 'problematic\-package\-0\.1\.0/beep boop\.ini"
        ),
    )

    # should report a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^6\. \[path\-contains\-spaces\] Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code[/]*"
        ),
    )

    # should report a file without spaces inside a directory with spaces
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^7\. \[path\-contains\-spaces\] Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code/__init__\.py"
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^8\. \[path\-contains\-spaces\] Found path with spaces\: "
            r"'problematic\-package\-0\.1\.0/problematic_package/bad code/ship\-it\.py"
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_unexpected_files_check_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1

    # directory
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^9\. \[unexpected\-files\] Found unexpected directory "
            r"'problematic\-package\-0\.1\.0/\.git[/]{0,1}'\."
        ),
    )

    # root-level files
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^10\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/\.gitignore'\."
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^11\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/\.hadolint\.yaml'\."
        ),
    )

    # nested files
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^12\. \[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/problematic_package/\.gitignore'\."
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_unexpected_files_correctly_respects_multiple_cli_args(distro_file):
    result = CliRunner().invoke(
        check,
        [
            os.path.join(TEST_DATA_DIR, distro_file),
            "--expected-files=!*.gitignore",
            "--expected-files=!*.git/HEAD",
            "--expected-directories=src/",
        ],
    )
    assert result.exit_code == 1

    # directories: should report that the expected directory was not found
    _assert_log_matches_pattern(
        result=result,
        pattern=r"\[expected\-files\] Did not find any directories matching pattern 'src/'",
    )

    # files: should find BOTH .gitignore files
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"\[unexpected\-files\] Found unexpected file 'problematic\-package\-0\.1\.0/\.gitignore"
        ),
    )
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"\[unexpected\-files\] Found unexpected file "
            r"'problematic\-package\-0\.1\.0/problematic_package/\.gitignore"
        ),
    )

    # files: should find the one .git/HEAD file
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"\[unexpected\-files\] Found unexpected file 'problematic\-package\-0\.1\.0/\.git/HEAD"
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]{1}"
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_expected_files_check_works(distro_file):
    result = CliRunner().invoke(
        check,
        [
            "--expected-files=*.R",
            "--expected-directories=Movies/*",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 1

    # directory
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^1\. \[expected\-files\] Did not find any directories matching pattern 'Movies/\*'."
        ),
    )

    # file
    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"^2\. \[expected\-files\] Did not find any files matching pattern '\*\.R'."
        ),
    )

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: [0-9]+"
    )


@pytest.mark.parametrize("distro_file", BASEBALL_PACKAGES)
def test_expected_files_does_not_raise_check_failure_if_all_patterns_match(distro_file):
    result = CliRunner().invoke(
        check,
        [
            # (wheel) lib/lib_baseball_metrics
            # (conda) lib/python3.9/site-packages/lib/lib_baseballmetrics.dylib
            "--expected-files=*/lib_baseballmetrics.*",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 0

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: 0"
    )


def test_expected_files_does_not_raise_check_failure_if_directory_pattern_matches():
    # conda packages, macOS wheels do not preserve directory members...
    # testing with a manylinux wheel to test that directory functionality works
    distro_file = f"baseballmetrics-0.1.0-py3-none-{MANYLINUX_SUFFIX}"
    result = CliRunner().invoke(
        check,
        [
            "--expected-directories=lib/",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 0

    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: 0"
    )


@pytest.mark.parametrize("distro_file", BASEBALL_CONDA_PACKAGES)
def test_path_too_long_check_works_for_conda_packages(distro_file):
    result = CliRunner().invoke(
        check,
        [
            "--max-path-length=5",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"\[path\-too\-long\] Path too long \(78 > 5\)\: "
            r"'lib/python3\.9/site\-packages/baseballmetrics/__pycache__/metrics\.cpython\-39\.pyc'"
        ),
    )


@pytest.mark.parametrize("distro_file", BASEBALL_WHEELS)
def test_path_too_long_check_works_for_wheels(distro_file):
    result = CliRunner().invoke(
        check,
        [
            "--max-path-length=5",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result=result,
        pattern=(
            r"\[path\-too\-long\] Path too long \(30 > 5\)\: "
            r"'baseballmetrics/_shared_lib\.py'"
        ),
    )


@pytest.mark.parametrize("distro_file", PROBLEMATIC_PACKAGES)
def test_cli_raises_exactly_the_expected_number_of_errors_for_the_problematic_package(
    distro_file,
):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1
    _assert_log_matches_pattern(
        result=result, pattern=r"errors found while checking\: 12$"
    )


@pytest.mark.parametrize("distro_file", PACKAGES_WITH_DEBUG_SYMBOLS)
def test_debug_symbols_check_works(distro_file):
    result = CliRunner().invoke(
        check,
        [os.path.join(TEST_DATA_DIR, distro_file)],
    )
    assert result.exit_code == 1, result.output
    if "macosx" in distro_file:
        # macOS wheels
        lib_file = r"\"lib/lib_baseballmetrics\.dylib\"'"
        if platform.startswith(("cygwin", "win")):
            debug_cmd = r"'llvm\-nm \-a " + lib_file
        else:
            # dsymutil works on both macOS and Linux
            debug_cmd = r"'dsymutil \-s " + lib_file
    elif "osx-64" in distro_file:
        # macOS conda packages
        lib_file = r"\"lib/python3\.9/site-packages/lib/lib_baseballmetrics\.dylib\"'\."
        if platform.startswith(("cygwin", "win")):
            debug_cmd = r"'llvm\-nm \-a " + lib_file
        else:
            # dsymutil works on both macOS and Linux
            debug_cmd = r"'dsymutil \-s " + lib_file
    elif NUMPY_WIN_DEBUG_WHL in distro_file:
        # windows wheels
        lib_file = r"\"numpy\.libs/libopenblas64__v0\.3\.23-293-gc2f4bdbb-gcc_10_3_0-2bde3a66a51006b2b53eb373ff767a3f\.dll\"'"
        debug_cmd = r"'objdump \-\-all\-headers " + lib_file
    else:
        # linux wheels
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
    result = CliRunner().invoke(
        check,
        [
            "--inspect",
            "--max-allowed-files=1",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 1

    _assert_log_matches_pattern(
        result, r"^1\. \[too\-many\-files\] Found 11 files\. Only 1 allowed\.$"
    )
    _assert_log_matches_pattern(result, "errors found while checking\\: 1")
    _assert_log_matches_pattern(result, r"^size by extension$")


def test_inspect_respects_output_file_size_unit_for_all_size_strings():
    distro_file = os.path.join(TEST_DATA_DIR, BASE_PACKAGES[0])

    # --output-file-size-unit auto
    result = CliRunner().invoke(
        check,
        [
            "--inspect",
            distro_file,
        ],
    )
    assert result.exit_code == 0

    # mix of B and K
    _assert_log_matches_pattern(result, r" compressed size: 4\.938K")
    _assert_log_matches_pattern(result, r" uncompressed size: 12\.039K")
    _assert_log_matches_pattern(result, r" \.py \- 70\.0B")
    _assert_log_matches_pattern(
        result, r" \(11\.092K\) base-package\-0\.1\.0/LICENSE\.txt"
    )

    # --output-file-size-unit B
    result = CliRunner().invoke(
        check,
        [
            "--inspect",
            "--output-file-size-unit=B",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 0

    # all B
    _assert_log_matches_pattern(result, r" compressed size: 5057\.0B")
    _assert_log_matches_pattern(result, r" uncompressed size: 12328\.0B")
    _assert_log_matches_pattern(result, r" \.py \- 70\.0B")
    _assert_log_matches_pattern(
        result, r" \(11358\.0B\) base-package\-0\.1\.0/LICENSE\.txt"
    )


def test_inspect_respects_output_file_size_precision_for_all_size_strings():
    distro_file = os.path.join(TEST_DATA_DIR, BASE_PACKAGES[0])

    # --output-file-size-unit auto
    result = CliRunner().invoke(
        check,
        [
            "--inspect",
            distro_file,
        ],
    )
    assert result.exit_code == 0

    # default precision
    _assert_log_matches_pattern(result, r" compressed size: 4\.938K")
    _assert_log_matches_pattern(result, r" uncompressed size: 12\.039K")
    _assert_log_matches_pattern(result, r" \.py \- 70\.0B")
    _assert_log_matches_pattern(
        result, r" \(11\.092K\) base-package\-0\.1\.0/LICENSE\.txt"
    )

    # --output-file-size-precision 2
    result = CliRunner().invoke(
        check,
        [
            "--inspect",
            "--output-file-size-precision=2",
            os.path.join(TEST_DATA_DIR, distro_file),
        ],
    )
    assert result.exit_code == 0

    # precision 2
    _assert_log_matches_pattern(result, r" compressed size: 4\.94K")
    _assert_log_matches_pattern(result, r" uncompressed size: 12\.04K")
    _assert_log_matches_pattern(result, r" \.py \- 70\.0B")
    _assert_log_matches_pattern(
        result, r" \(11\.09K\) base-package\-0\.1\.0/LICENSE\.txt"
    )
