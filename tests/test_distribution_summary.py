import os
import zipfile

import pytest

from pydistcheck.distribution_summary import _DistributionSummary, _FileInfo

BASE_PACKAGE_SDISTS = ["base-package-0.1.0.tar.gz", "base-package-0.1.0.zip"]
MACOS_SUFFIX = "macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl"
MANYLINUX_SUFFIX = "manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl"
BASE_WHEELS = [
    f"baseballmetrics-0.1.0-py3-none-{MACOS_SUFFIX}",
    f"baseballmetrics-0.1.0-py3-none-{MANYLINUX_SUFFIX}",
]
WINDOWS_WHEELS = ["lightgbm-3.3.5-py3-none-win_amd64.whl"]
TEST_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


@pytest.mark.parametrize("distro_file", BASE_PACKAGE_SDISTS)
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
    assert ds.compiled_objects == []
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


@pytest.mark.parametrize("distro_file", BASE_WHEELS)
def test_distribution_summary_correctly_reads_contents_of_wheels(distro_file):
    ds = _DistributionSummary.from_file(os.path.join(TEST_DATA_DIR, distro_file))

    # should correctly capture the contents:
    #   * 4 directories
    #   * 8 files
    assert len(ds.files) == 8
    assert ds.num_files == 8

    # `pip wheel` seems to omit directory members from the archive,
    # and `auditwheel repair` seems to restore them
    #
    # so this project's test macOS wheels don't have directory members
    if "macosx" in distro_file:
        expected_dir_paths = []
        expected_file_format = "Mach-O"
        expected_num_directories = 0
        shared_lib_ext = "dylib"
    else:
        expected_dir_paths = [
            "baseballmetrics-0.1.0.dist-info/",
            "baseballmetrics.libs/",
            "baseballmetrics/",
            "lib/",
        ]
        expected_file_format = "ELF"
        expected_num_directories = 4
        shared_lib_ext = "so"

    assert len(ds.directories) == expected_num_directories
    assert ds.num_directories == expected_num_directories

    expected_file_paths = [
        "baseballmetrics-0.1.0.dist-info/METADATA",
        "baseballmetrics-0.1.0.dist-info/RECORD",
        "baseballmetrics-0.1.0.dist-info/WHEEL",
        "baseballmetrics-0.1.0.dist-info/entry_points.txt",
        "baseballmetrics/__init__.py",
        "baseballmetrics/_shared_lib.py",
        "baseballmetrics/metrics.py",
        f"lib/lib_baseballmetrics.{shared_lib_ext}",
    ]

    expected_all_paths = expected_dir_paths + expected_file_paths

    assert sorted(ds.all_paths) == sorted(expected_all_paths)

    # pulling this _FileInfo object out and comparing attribute-by-attribute,
    # to avoid needing to change the test when the library size changes
    assert len(ds.compiled_objects) == 1
    lib_file_info = ds.compiled_objects[0]
    assert lib_file_info.name == f"lib/lib_baseballmetrics.{shared_lib_ext}"
    assert lib_file_info.file_format == expected_file_format
    assert lib_file_info.file_extension == f".{shared_lib_ext}"
    assert lib_file_info.is_compiled is True

    assert sorted(ds.directory_paths) == sorted(expected_dir_paths)
    assert sorted(ds.file_paths) == sorted(expected_file_paths)

    # total archive sizes should make sense
    assert ds.compressed_size_bytes > 0
    assert ds.compressed_size_bytes < 6e3
    assert ds.uncompressed_size_bytes > 0
    assert ds.uncompressed_size_bytes > ds.compressed_size_bytes

    # size_by_file_extension should work as expected
    if "macosx" in distro_file:
        assert ds.size_by_file_extension == {
            ".dylib": 16504,
            "no-extension": 824,
            ".py": 536,
            ".txt": 0,
        }
    else:
        assert ds.size_by_file_extension == {
            ".so": 15616,
            "no-extension": 902,
            ".py": 536,
            ".txt": 0,
        }

    # size_by_file_extension should return results sorted from largest to smallest by file size
    last_size_seen = float("inf")
    for _, size_in_bytes in ds.size_by_file_extension.items():
        assert size_in_bytes < last_size_seen
        last_size_seen = size_in_bytes


@pytest.mark.parametrize("distro_file", [*BASE_WHEELS, *WINDOWS_WHEELS])
def test_file_info_correctly_determines_file_type(distro_file):
    full_path = os.path.join(TEST_DATA_DIR, distro_file)
    if "macosx" in distro_file:
        expected_file_format = "Mach-O"
        shared_lib_file = "lib/lib_baseballmetrics.dylib"
    elif "manylinux" in distro_file:
        expected_file_format = "ELF"
        shared_lib_file = "lib/lib_baseballmetrics.so"
    else:
        expected_file_format = "Windows PE"
        shared_lib_file = "lightgbm/lib_lightgbm.dll"
    with zipfile.ZipFile(full_path, mode="r") as zf:
        zip_info = zf.getinfo(shared_lib_file)
        file_info = _FileInfo.from_zipfile_member(archive_file=zf, zip_info=zip_info)
        assert file_info.is_compiled is True
        assert file_info.file_format == expected_file_format
