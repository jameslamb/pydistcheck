"""
Tests that ensure documentation accurately describes the
state of the project's source code.
"""

from pathlib import Path

from pydistcheck._compat import tomllib
from pydistcheck.checks import ALL_CHECKS
from pydistcheck.config import _ALLOWED_CONFIG_VALUES, _Config

DOCS_ROOT = Path(__file__).parents[1].joinpath("docs")


def test_default_toml_config():
    # NOTE: this intentionally does not use pydistcheck._Config.update_from_toml(),
    #       to ensure that's bugs in that class don't also cause this test to accidentally pass.
    defaults_example_file = DOCS_ROOT.joinpath("_static/defaults.toml")
    with open(defaults_example_file, "rb") as f:
        config_dict = tomllib.load(f)
        tool_options = config_dict.get("tool", {}).get("pydistcheck", {})

    opts_in_docs = set(tool_options.keys())
    missing_opts = _ALLOWED_CONFIG_VALUES - opts_in_docs
    assert len(missing_opts) == 0, f"missing options: {','.join(missing_opts)}"
    extra_opts = opts_in_docs - _ALLOWED_CONFIG_VALUES
    assert len(extra_opts) == 0, f"unrecognized options: {','.join(extra_opts)}"

    # values should exactly match the defaults
    config = _Config().update_from_toml(defaults_example_file)
    assert (
        config == _Config()
    ), "values in 'docs/_static/defaults.toml' do not match actual defaults used by pydistcheck"


def test_all_checks_are_documented_in_check_reference():
    check_ref_file = DOCS_ROOT.joinpath("check-reference.rst")
    with open(check_ref_file, "r") as f:
        check_ref_str = f.read()

    for check in ALL_CHECKS:
        assert (
            f"\n\n{check}\n****" in check_ref_str
        ), f"'{check}' not yet documented in 'docs/check-reference.rst'"
