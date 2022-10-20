import os
import pytest

from pydistcheck.distribution_summary import _DistributionSummary

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.mark.parametrize("distro_file", ["base-package.tar.gz", "base-package.zip"])
def test_distribution_summary_basically_works(distro_file):
    ds = _DistributionSummary.from_file(os.path.join(TEST_DATA_DIR, distro_file))

    # size should basically make sense
    assert ds.compressed_size_bytes > 0
    assert ds.compressed_size_bytes < 1e8

    # should correctly capture the contents:
    #   * 1 directory
    #   * 3 files
    assert len(ds.file_infos) == 4
    assert len([f for f in ds.file_infos if f.is_directory]) == 1
    assert ds.num_directories == 1
    assert len([f for f in ds.file_infos if not f.is_directory]) == 3
    assert ds.num_files == 3

    # compression ratio should make sense
    #
    # NOTE: it is POSSIBLE, but that should be rare for Python
    #       distribution files
    assert ds.compressed_size_bytes > 0
    assert ds.uncompressed_size_bytes > 0
    assert ds.uncompressed_size_bytes > ds.compressed_size_bytes
    assert ds.compression_ratio > 0.1
    assert ds.compression_ratio <= 0.9

    # size_by_file_extension should work as expected
    assert ds.size_by_file_extension == {".py": 32, ".txt": 11358}
