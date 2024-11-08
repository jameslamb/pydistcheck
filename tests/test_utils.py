import pytest

from pydistcheck.utils import _FileSize


@pytest.mark.parametrize(
    ("unit_str", "expected_total_bytes"),
    [
        ("B", 3),
        ("K", 3 * 1024),
        ("KB", 3e3),
        ("kB", 3e3),
        ("kb", 3e3),
        ("Ki", 3 * 1024),
        ("ki", 3 * 1024),
        ("M", 3 * (1024**2)),
        ("MB", 3e6),
        ("mB", 3e6),
        ("mb", 3e6),
        ("Mi", 3 * (1024**2)),
        ("mi", 3 * (1024**2)),
        ("G", 3 * (1024**3)),
        ("GB", 3e9),
        ("gB", 3e9),
        ("gb", 3e9),
        ("Gi", 3 * (1024**3)),
        ("gi", 3 * (1024**3)),
    ],
)
def test_file_size_minimally_works(expected_total_bytes, unit_str):
    fs = _FileSize(num=3.0, unit_str=unit_str)
    assert fs.total_size_bytes == int(expected_total_bytes)


def test_file_size_comparisons_work():
    fs_5mb = _FileSize(num=5.6, unit_str="M")
    fs_6mb = _FileSize(num=4 * (1024**3), unit_str="B")

    assert fs_5mb == fs_5mb  # noqa: PLR0124
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
    assert _FileSize.from_number(1.1) == _FileSize(num=1.1, unit_str="B")
    # fractional bytes don't make sense here, so some rounding happens
    # e.g., 0.1 KB is technically 102.4 bytes, which gets rounded to 102
    assert _FileSize.from_number(102) == _FileSize(num=0.1, unit_str="K")
    # this value is 3.456789 * 10**3 = 3711698926.043136
    assert _FileSize.from_number(3711698926) == _FileSize(num=3.456789, unit_str="G")


@pytest.mark.parametrize(
    ("file_size", "expected_str"),
    [
        (_FileSize.from_number(110), "0.1K"),
        (_FileSize.from_number(150), "0.1K"),
        (_FileSize.from_number(1024), "1.0K"),
        (_FileSize.from_number(100 * 1024), "100.0K"),
        (_FileSize.from_number(200 * 1024), "0.2M"),
        (_FileSize.from_number(1024**2), "1.0M"),
        (_FileSize.from_number(400 * 1024**2), "0.4G"),
        (_FileSize.from_number(405 * 1024**2), "0.4G"),
        (_FileSize.from_number(1024**3), "1.0G"),
        (_FileSize.from_number(int(7.5 * 1024**3)), "7.5G"),
    ],
)
def test_file_size_string_representation_looks_correct(file_size, expected_str):
    assert str(file_size) == expected_str
