from pydistcheck.utils import _FileSize


def test_file_size_minimally_works():
    fs = _FileSize(num=1.0, unit_str="G")
    assert fs.total_size_bytes == int(1024**3)


def test_file_size_comparisons_work():
    fs_5mb = _FileSize(num=5.6, unit_str="M")
    fs_6mb = _FileSize(num=6 * (1024**1024), unit_str="B")

    assert fs_5mb != fs_6mb
