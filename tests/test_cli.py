import os
import pytest

from click.testing import CliRunner
from pydistcheck.cli import check

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


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

    log_lines = result.output.split("\n")
    assert "1. [too-many-files] Found 2 files. Only 1 allowed." in log_lines
    assert "errors found while checking: 1" in log_lines
