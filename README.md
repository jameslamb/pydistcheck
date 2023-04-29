# pydistcheck

[![conda-forge version](https://img.shields.io/conda/vn/conda-forge/pydistcheck.svg)](https://anaconda.org/conda-forge/pydistcheck)
[![conda-forge downloads](https://img.shields.io/conda/dn/conda-forge/pydistcheck.svg)](https://anaconda.org/conda-forge/pydistcheck)
[![PyPI Version](https://img.shields.io/pypi/v/pydistcheck.svg?logo=pypi&logoColor=white)](https://pypi.org/project/pydistcheck)
[![PyPI downloads](https://static.pepy.tech/badge/pydistcheck)](https://pypi.org/project/pydistcheck)
[![Documentation Status](https://readthedocs.org/projects/pydistcheck/badge/?version=latest)](https://pydistcheck.readthedocs.io/)
[![GitHub Actions](https://github.com/jameslamb/pydistcheck/workflows/unit-tests/badge.svg?branch=main)](https://github.com/jameslamb/pydistcheck/actions/workflows/unit-tests.yml)
[![GitHub Actions](https://github.com/jameslamb/pydistcheck/workflows/smoke-tests/badge.svg?branch=main)](https://github.com/jameslamb/pydistcheck/actions/workflows/smoke-tests.yml)

## What is `pydistcheck`?

`pydistcheck` is a command line interface (CLI) for:

* inspecting the contents of Python package distributions during development
* enforcing constraints on Python package distributions in continuous integration

It's inspired by R's `R CMD check`.

For more background on the value of such a tool, see the SciPY 2022 talk "Does that CSV Belong on PyPI? Probably Not" ([video link](https://www.youtube.com/watch?v=1a7g5l_g_U8)).

## Installation

Install with `pipx`.

```shell
pipx install pydistcheck
```

## Quickstart

Try it out on the test data in this project ...

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
pydistcheck tests/data/debug-baseballmmetrics*.whl
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

## Related Projects

* https://pypi.org/project/inspect4py/
* https://github.com/regebro/pyroma

## References

* Python packaging guides: https://packaging.python.org/en/latest/guides/#
