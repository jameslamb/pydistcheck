# pydistcheck

[![conda-forge version](https://img.shields.io/conda/vn/conda-forge/pydistcheck.svg)](https://anaconda.org/conda-forge/pydistcheck)
[![conda-forge downloads](https://img.shields.io/conda/dn/conda-forge/pydistcheck.svg)](https://anaconda.org/conda-forge/pydistcheck)
[![PyPI Version](https://img.shields.io/pypi/v/pydistcheck.svg?logo=pypi&logoColor=white)](https://pypi.org/project/pydistcheck)
[![PyPI downloads](https://static.pepy.tech/badge/pydistcheck)](https://pypi.org/project/pydistcheck)
[![Documentation Status](https://readthedocs.org/projects/pydistcheck/badge/?version=latest)](https://pydistcheck.readthedocs.io/)
[![GitHub Actions](https://github.com/jameslamb/pydistcheck/actions/workflows/unit-tests.yml/badge.svg?branch=main)](https://github.com/jameslamb/pydistcheck/actions/workflows/unit-tests.yml)
[![GitHub Actions](https://github.com/jameslamb/pydistcheck/actions/workflows/smoke-tests.yml/badge.svg?branch=main)](https://github.com/jameslamb/pydistcheck/actions/workflows/smoke-tests.yml)

## What is `pydistcheck`?

`pydistcheck` is a command line interface (CLI) that you run on Python packages, which can:

* detect common portability issues
* print useful summaries of the package's contents

It's inspired by R's `R CMD check`.

Supported formats:

* Python sdists
* Python wheels
* `conda` packages (both `.conda` and `.tar.bz2`)
* any `.tar.bz2`, `.tar.gz`, or `.zip` archive

See ["Check Reference"](https://pydistcheck.readthedocs.io/en/latest/check-reference.html) for a complete list of the types of issues `pydistcheck` can catch.

See ["How to Test a Python Distribution"](https://pydistcheck.readthedocs.io/en/latest/how-to-test-a-python-distribution.html) to learn how `pydistcheck` and similar tools like [`auditwheel`](https://github.com/pypa/auditwheel), [`check-wheel-contents`](https://github.com/jwodder/check-wheel-contents), and [`twine check`](https://twine.readthedocs.io/en/stable/#twine-check) fit into Python development workflows.

For more background on the value of such a tool, see the SciPy 2022 talk "Does that CSV Belong on PyPI? Probably Not" ([video link](https://www.youtube.com/watch?v=1a7g5l_g_U8)).

## Installation

Install with `pip`.

```shell
pip install pydistcheck
```

Or `conda`.

```shell
conda install -c conda-forge pydistcheck
```

For more details, see "Installation" ([link](./docs/installation.rst)).

## Quickstart

Try it out on a package you like...

```shell
pip download \
  --no-deps \
  -d ./downloads \
  pyarrow

pydistcheck --inspect ./downloads/*.whl
```

... to see what it contains.

```text
----- package inspection summary -----
file size
  * compressed size: 25.9M
  * uncompressed size: 94.0M
  * compression space saving: 72.4%
contents
  * directories: 0
  * files: 809 (30 compiled)
size by extension
  * .dylib - 73.2M (77.9%)
  * .so - 10.8M (11.4%)
  * .h - 4.5M (4.8%)
  * .py - 2.4M (2.5%)
  * .pyx - 0.8M (0.8%)
  * .pxi - 0.7M (0.8%)
  * .cc - 0.4M (0.5%)
  * .cmake - 0.4M (0.4%)
  * .pxd - 0.3M (0.3%)
  * .gz - 0.2M (0.2%)
  * .hpp - 0.1M (0.1%)
  * .txt - 0.1M (0.1%)
  * no-extension - 77.4K (0.1%)
  * .orc - 48.4K (0.1%)
  * .parquet - 14.0K (0.0%)
  * .sh - 7.8K (0.0%)
  * .md - 3.6K (0.0%)
  * .yml - 1.5K (0.0%)
  * .ubuntu - 1.3K (0.0%)
  * .fedora - 1.0K (0.0%)
  * .diff - 1.0K (0.0%)
  * .feather - 0.6K (0.0%)
largest files
  * (49.1M) pyarrow/libarrow.1700.dylib
  * (10.7M) pyarrow/libarrow_flight.1700.dylib
  * (3.8M) pyarrow/lib.cpython-311-darwin.so
  * (3.8M) pyarrow/libparquet.1700.dylib
  * (2.9M) pyarrow/libarrow_substrait.1700.dylib

==================== done running pydistcheck ===============
```

Or on the test data in this repo ...

```shell
pydistcheck tests/data/problematic-package-*
```

... to see the types of issues it checks for.

```text
------------ check results -----------
1. [files-only-differ-by-case] Found files which differ only by case. Files: problematic-package-0.1.0/problematic_package/Question.py,problematic-package-0.1.0/problematic_package/question.PY,problematic-package-0.1.0/problematic_package/question.py
2. [mixed-file-extensions] Found a mix of file extensions for the same file type: .NDJSON (1), .jsonl (1), .ndjson (1)
3. [mixed-file-extensions] Found a mix of file extensions for the same file type: .yaml (2), .yml (1)
4. [path-contains-non-ascii-characters] Found file path containing non-ASCII characters: 'problematic-package-0.1.0/problematic_package/?veryone-loves-python.py'
5. [path-contains-spaces] Found path with spaces: 'problematic-package-0.1.0/beep boop.ini'
6. [path-contains-spaces] Found path with spaces: 'problematic-package-0.1.0/problematic_package/bad code/'
7. [path-contains-spaces] Found path with spaces: 'problematic-package-0.1.0/problematic_package/bad code/__init__.py'
8. [path-contains-spaces] Found path with spaces: 'problematic-package-0.1.0/problematic_package/bad code/ship-it.py'
9. [unexpected-files] Found unexpected directory 'problematic-package-0.1.0/.git/'.
10. [unexpected-files] Found unexpected file 'problematic-package-0.1.0/.gitignore'.
11. [unexpected-files] Found unexpected file 'problematic-package-0.1.0/.hadolint.yaml'.
12. [unexpected-files] Found unexpected file 'problematic-package-0.1.0/problematic_package/.gitignore'.
errors found while checking: 12
```

And on a built distribution containing compiled objects ...

```shell
pydistcheck tests/data/debug-baseballmetrics*.whl
```

... `pydistcheck` can detect the inclusion of debug symbols (which increase distribution size).

```text
checking 'tests/data/debug-baseballmetrics-0.1.0-py3-none-macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl'
------------ check results -----------
1. [compiled-objects-have-debug-symbols] Found compiled object containing debug symbols. For details, extract the distribution contents and run 'dsymutil -s "lib/lib_baseballmetrics.dylib"'.
errors found while checking: 1

checking 'tests/data/debug-baseballmetrics-py3-none-manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl'
------------ check results -----------
1. [compiled-objects-have-debug-symbols] Found compiled object containing debug symbols. For details, extract the distribution contents and run 'objdump --all-headers "lib/lib_baseballmetrics.so"'.
errors found while checking: 1
```

See https://pydistcheck.readthedocs.io/en/latest/ to learn more.

## References

* Python packaging guides: https://packaging.python.org/en/latest/guides/#
