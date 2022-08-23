import os
import pytest

from click.testing import CliRunner
from pydistcheck.cli import check

TEST_DIR = os.path.abspath(__file__)


@parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_check_runs_without_error(tmp_path, distro_file):
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        result = runner.invoke(check, [os.path.join(TEST_DIR, distro_file)])
        assert result.exit_code == 0
