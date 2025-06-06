import os
import uuid
from copy import deepcopy
from dataclasses import fields

import pytest

from pydistcheck._config import _ALLOWED_CONFIG_VALUES, _Config


@pytest.fixture(scope="function")
def base_config():
    return _Config(
        inspect=False,
        max_allowed_files=7,
        max_allowed_size_compressed="1G",
        max_allowed_size_uncompressed="18K",
    )


def test_allowed_config_values_constant_matches_class():
    fields_from_class = {f.name for f in fields(_Config)}
    assert fields_from_class == _ALLOWED_CONFIG_VALUES


def test_config_fixture_works_as_expected(base_config):
    assert base_config.inspect is False
    assert base_config.max_allowed_files == 7
    assert base_config.max_allowed_size_compressed == "1G"
    assert base_config.max_allowed_size_uncompressed == "18K"


def test_config_can_be_initialized_without_any_arguments():
    config = _Config()
    assert config.inspect is False
    assert config.max_allowed_files == 2000
    assert config.max_allowed_size_compressed == "50M"
    assert config.max_allowed_size_uncompressed == "75M"


def test_update_from_dict_raises_exception_for_first_bad_value_encountered(base_config):
    with pytest.raises(
        ValueError, match=r"Configuration value 'a' is not recognized by pydistcheck"
    ):
        base_config.update_from_dict({"a": 7, "b": 8, "inspect": False})


def test_update_from_dict_works_even_if_dict_does_not_include_all_config_values(
    base_config,
):
    assert base_config.inspect is False
    base_config.update_from_dict({"inspect": True})
    assert base_config.inspect is True


def test_update_from_dict_works_when_changing_all_values(base_config):
    assert base_config.ignore == ()
    assert base_config.inspect is False
    assert base_config.max_allowed_files == 7
    assert base_config.max_allowed_size_compressed == "1G"
    assert base_config.max_allowed_size_uncompressed == "18K"
    assert base_config.output_file_size_precision == 3
    assert base_config.output_file_size_unit == "auto"
    assert base_config.select == ()
    patch_dict = {
        "expected_directories": "!*/tests",
        "expected_files": "!*.xlsx,!data/*.csv",
        "ignore": ["path-contains-spaces", "too-many-files"],
        "inspect": True,
        "max_allowed_files": 8,
        "max_allowed_size_compressed": "2G",
        "max_allowed_size_uncompressed": "141K",
        "max_path_length": 600,
        "output_file_size_precision": 2,
        "output_file_size_unit": "GB",
        "select": ["distro-too-large-compressed"],
    }
    assert set(patch_dict.keys()) == _ALLOWED_CONFIG_VALUES, (
        "this test needs to be updated"
    )
    base_config.update_from_dict(patch_dict)
    assert base_config.expected_directories == "!*/tests"
    assert base_config.expected_files == "!*.xlsx,!data/*.csv"
    assert base_config.ignore == ["path-contains-spaces", "too-many-files"]
    assert base_config.inspect is True
    assert base_config.max_allowed_files == 8
    assert base_config.max_allowed_size_compressed == "2G"
    assert base_config.max_allowed_size_uncompressed == "141K"
    assert base_config.max_path_length == 600
    assert base_config.output_file_size_precision == 2
    assert base_config.output_file_size_unit == "GB"
    assert base_config.select == ["distro-too-large-compressed"]


def test_update_from_toml_silently_returns_self_if_file_does_not_exist(base_config):
    original_config = deepcopy(base_config)
    out = base_config.update_from_toml(toml_file=f"{uuid.uuid4().hex}.toml")
    assert out == original_config


def test_update_from_toml_works_for_files_with_no_pydistcheck_configuration(
    base_config, tmpdir
):
    original_config = deepcopy(base_config)
    temp_file = os.path.join(tmpdir, f"{uuid.uuid4().hex}.toml")
    with open(temp_file, "w") as f:
        f.write("""[tool.pylint]\n""")
    base_config.update_from_toml(toml_file=temp_file)
    assert base_config == original_config


def test_update_from_toml_works_for_files_with_empty_pydistcheck_configuration(
    base_config, tmpdir
):
    original_config = deepcopy(base_config)
    temp_file = os.path.join(tmpdir, f"{uuid.uuid4().hex}.toml")
    with open(temp_file, "w") as f:
        f.write("""\n[tool.pylint]\n[tool.pydistcheck]\n""")
    base_config.update_from_toml(toml_file=temp_file)
    assert base_config == original_config


@pytest.mark.parametrize(
    "config_key", ["max_allowed_size_compressed", "max-allowed-size_compressed"]
)
def test_update_from_toml_works_with_underscores_and_hyphens(
    base_config, tmpdir, config_key
):
    temp_file = os.path.join(tmpdir, f"{uuid.uuid4().hex}.toml")
    with open(temp_file, "w") as f:
        f.write(f"[tool.pylint]\n[tool.pydistcheck]\n{config_key} = '2.5G'\n")
    base_config.update_from_toml(toml_file=temp_file)
    assert base_config.max_allowed_size_compressed == "2.5G"


@pytest.mark.parametrize("use_hyphens", [True, False])
def test_update_from_toml_works_with_all_config_values(
    base_config, tmpdir, use_hyphens
):
    temp_file = os.path.join(tmpdir, f"{uuid.uuid4().hex}.toml")
    patch_dict = {
        "expected_directories": "[\n'!tests/*'\n]",
        "expected_files": "[\n'!*.pq',\n'!*/tests/data/*.csv']",
        "ignore": "[\n'path-contains-spaces',\n'too-many-files'\n]",
        "inspect": "true",
        "max_allowed_files": 8,
        "max_allowed_size_compressed": "'3G'",
        "max_allowed_size_uncompressed": "'4.12G'",
        "max_path_length": 25,
        "output_file_size_precision": 2,
        "output_file_size_unit": "'Mi'",
        "select": "[\n'mixed-file-extensions',\n'path-contains-non-ascii-characters'\n]",
    }
    assert set(patch_dict.keys()) == _ALLOWED_CONFIG_VALUES, (
        "this test needs to be updated"
    )
    if use_hyphens:
        patch_dict = {k.replace("_", "-"): v for k, v in patch_dict.items()}
    with open(temp_file, "w") as f:
        lines = ["[tool.pylint]", "[tool.pydistcheck]"] + [
            f"{k} = {v}" for k, v in patch_dict.items()
        ]
        f.write("\n".join(lines))
    base_config.update_from_toml(toml_file=temp_file)
    assert base_config.expected_directories == ["!tests/*"]
    assert base_config.expected_files == ["!*.pq", "!*/tests/data/*.csv"]
    assert base_config.ignore == ["path-contains-spaces", "too-many-files"]
    assert base_config.inspect is True
    assert base_config.max_allowed_files == 8
    assert base_config.max_allowed_size_compressed == "3G"
    assert base_config.max_allowed_size_uncompressed == "4.12G"
    assert base_config.max_path_length == 25
    assert base_config.output_file_size_precision == 2
    assert base_config.output_file_size_unit == "Mi"
    assert base_config.select == [
        "mixed-file-extensions",
        "path-contains-non-ascii-characters",
    ]
