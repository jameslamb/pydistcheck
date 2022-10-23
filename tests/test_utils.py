import pytest

from pydistcheck.utils import _FileSize


def test_file_size_minimally_works():
    fs = _FileSize(num=1.0, unit_str="G")
    assert fs.total_size_bytes == int(1024**3)


def test_file_size_comparisons_work():
    fs_5mb = _FileSize(num=5.6, unit_str="M")
    fs_6mb = _FileSize(num=4 * (1024**3), unit_str="B")

    assert fs_5mb == fs_5mb
    assert fs_5mb != fs_6mb
    assert fs_5mb != fs_6mb
    assert fs_5mb < fs_6mb
    assert fs_5mb <= fs_6mb
    assert fs_6mb >= fs_5mb
    assert fs_6mb > fs_5mb


@pytest.mark.parametrize(
    "file_size",
    [
        _FileSize.from_number(3 * 1024**2),
        _FileSize.from_string("3M"),
        _FileSize.from_string("3.0M"),
        _FileSize.from_string("3.0000M"),
    ],
)
def test_file_size_from_different_inputs_all_parsed_consistently(file_size):
    assert file_size == _FileSize(num=3.0, unit_str="M")


def test_file_size_from_number_switches_unit_str_based_on_size():
    _FileSize.from_number(1.1) == _FileSize(num=1.1, unit_str="B")
    _FileSize.from_number(100.01) == _FileSize(num=0.10001, unit_str="K")
    _FileSize.from_number(3456789) == _FileSize(num=3.456789, unit_str="G")
