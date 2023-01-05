import os

import pytest

from pydistcheck.distribution_summary import _DistributionSummary

TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.mark.parametrize("distro_file", ["base-package-0.1.0.tar.gz", "base-package-0.1.0.zip"])
def test_distribution_summary_basically_works(distro_file):
    ds = _DistributionSummary.from_file(os.path.join(TEST_DATA_DIR, distro_file))

    # should correctly capture the contents:
    #   * 3 directories
    #   * 11 files
    assert len(ds.files) == 11
    assert ds.num_files == 11
    assert len(ds.directories) == 3
    assert ds.num_directories == 3

    # file_paths should include all the files and directories
    # (NOTE: zip adds trailing slashes to directories, tar does not)
    if distro_file.endswith("zip"):
        expected_dir_paths = [
            "base-package-0.1.0/",
            "base-package-0.1.0/base_package/",
            "base-package-0.1.0/base_package.egg-info/",
        ]
    else:
        expected_dir_paths = [
            "base-package-0.1.0",
            "base-package-0.1.0/base_package",
            "base-package-0.1.0/base_package.egg-info",
        ]
    expected_file_paths = [
        "base-package-0.1.0/setup.cfg",
        "base-package-0.1.0/PKG-INFO",
        "base-package-0.1.0/setup.py",
        "base-package-0.1.0/LICENSE.txt",
        "base-package-0.1.0/README.md",
        "base-package-0.1.0/base_package/__init__.py",
        "base-package-0.1.0/base_package/thing.py",
        "base-package-0.1.0/base_package.egg-info/top_level.txt",
        "base-package-0.1.0/base_package.egg-info/dependency_links.txt",
        "base-package-0.1.0/base_package.egg-info/SOURCES.txt",
        "base-package-0.1.0/base_package.egg-info/PKG-INFO",
    ]
    expected_all_paths = expected_dir_paths + expected_file_paths

    assert sorted(ds.all_paths) == sorted(expected_all_paths)
    assert sorted(ds.directory_paths) == sorted(expected_dir_paths)
    assert sorted(ds.file_paths) == sorted(expected_file_paths)

    # total archive sizes should make sense
    assert ds.compressed_size_bytes > 0
    assert ds.compressed_size_bytes < 1e8
    assert ds.uncompressed_size_bytes > 0
    assert ds.uncompressed_size_bytes > ds.compressed_size_bytes

    # size_by_file_extension should work as expected
    assert ds.size_by_file_extension == {
        ".cfg": 258,
        ".md": 15,
        "no-extension": 382,
        ".py": 70,
        ".txt": 11603,
    }

    # size_by_file_extension should return results sorted from largest to smallest by file size
    last_size_seen = float("inf")
    for _, size_in_bytes in ds.size_by_file_extension.items():
        assert size_in_bytes < last_size_seen
        last_size_seen = size_in_bytes


def test_distribution_summary_correctly_reads_contents_of_wheels():
    wheel_file = (
        "baseballmetrics-0.1.0-"
        "py3-none-manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl"
    )
    ds = _DistributionSummary.from_file(os.path.join(TEST_DATA_DIR, wheel_file))

    # should correctly capture the contents:
    #   * 4 directories
    #   * 8 files
    assert len(ds.files) == 8
    assert ds.num_files == 8
    assert len(ds.directories) == 4
    assert ds.num_directories == 4

    expected_dir_paths = [
        "baseballmetrics-0.1.0.dist-info/",
        "baseballmetrics.libs/",
        "baseballmetrics/",
        "baseballmetrics/lib/",
    ]
    expected_file_paths = [
        "baseballmetrics-0.1.0.dist-info/METADATA",
        "baseballmetrics-0.1.0.dist-info/RECORD",
        "baseballmetrics-0.1.0.dist-info/WHEEL",
        "baseballmetrics-0.1.0.dist-info/top_level.txt",
        "baseballmetrics/__init__.py",
        "baseballmetrics/_shared_lib.py",
        "baseballmetrics/lib/lib_baseballmetrics.so",
        "baseballmetrics/metrics.py",
    ]

    expected_all_paths = expected_dir_paths + expected_file_paths

    assert sorted(ds.all_paths) == sorted(expected_all_paths)
    assert sorted(ds.directory_paths) == sorted(expected_dir_paths)
    assert sorted(ds.file_paths) == sorted(expected_file_paths)

    # total archive sizes should make sense
    assert ds.compressed_size_bytes > 0
    assert ds.compressed_size_bytes < 6e3
    assert ds.uncompressed_size_bytes > 0
    assert ds.uncompressed_size_bytes > ds.compressed_size_bytes

    # size_by_file_extension should work as expected
    assert ds.size_by_file_extension == {
        ".so": 15616,
        "no-extension": 1191,
        ".py": 414,
        ".txt": 33,
    }

    # size_by_file_extension should return results sorted from largest to smallest by file size
    last_size_seen = float("inf")
    for _, size_in_bytes in ds.size_by_file_extension.items():
        assert size_in_bytes < last_size_seen
        last_size_seen = size_in_bytes
