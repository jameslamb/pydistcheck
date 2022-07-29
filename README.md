# pydistcheck

[![GitHub Actions](https://github.com/jameslamb/pydistcheck/workflows/tests/badge.svg?branch=main)](https://github.com/jameslamb/pydistcheck/actions)

> **Warning**
>
> This project is very-very-very new and will change significantly.
> The next time you look at this repo, this might not even be written in the same programming language.
> If I was you, **I wouldn't use it**.

Analyzes the contents of a Python package and warns about common issues, like:

* inclusion of unnecessary files
* use of multiple file extensions with the same meaning

## Minimal Example

Get information about the files associated with the most recent release of a package to PyPI.

```shell
make full-run \
    -e PACKAGE_NAME=lightgbm
```

or, using the CLI

```shell
make build install

pydistcheck summarize \
  --file dist/pydistcheck*.tar.gz \
  --output-file "$(pwd)/sizes.csv"
```

Questions to be answered?

* what are the `n` largest files in this artifact?
* what is the total size (compressed and uncompressed) of this artifact?
* what file types (by extension) exist in this artifact? how much space do they take up?

Ideas for a file content linter:

* mixes of extensions for the same file type (e.g. `.yaml` and `.yml`)
* file types not expected to be found in a Python package
* executable files
* a directory called "tests/"

## Related Projects

* https://pypi.org/project/inspect4py/

## References

* Python packaging guides: https://packaging.python.org/en/latest/guides/#
* PyPI APIs: https://warehouse.pypa.io/api-reference/index.html
* https://gitlab.com/n2vram/tarwalker/-/blob/master/tarwalker.py
* https://cibuildwheel.readthedocs.io/en/stable/deliver-to-pypi/
    - https://cibuildwheel.readthedocs.io/en/stable/options/
* https://github.com/pypa/cibuildwheel/blob/main/examples/github-deploy.yml
* https://github.com/pypa/auditwheel
* https://github.com/matthew-brett/delocate
* https://setuptools.pypa.io/en/latest/userguide/entry_point.html
