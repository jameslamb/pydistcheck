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

## Minimal Example

Given a Python distribution...

```shell
pydistcheck dist/*
```

## Related Projects

* https://pypi.org/project/inspect4py/
* https://github.com/regebro/pyroma

## References

* Python packaging guides: https://packaging.python.org/en/latest/guides/#
