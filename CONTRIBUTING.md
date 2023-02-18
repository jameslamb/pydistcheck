# contributing

## Building the package

This project uses `pipx` to run other Python-based CLIs.
Follow https://github.com/pypa/pipx#install-pipx to install it.

Then run the following.

```shell
make build install
```

## Releasing

1. Open a pull request with title `release v{major}.{minor}.{patch}`, changing `version` in `pyproject.toml` to the desired version.
2. navigate to https://github.com/jameslamb/pydistcheck/releases
3. edit the draft release there
    - remove any changelog items that are just "changed the version number" PRs
    - ensure that the tag that'll be created matches the version number, in the form `v{major}.{minor}.{patch}`
4. click "publish"
    - when that happens, CI jobs will run that automatically publish the package to PyPI.
5. Open another pull request with title `bump development version` adding `.99` to the version in `pyproject.toml`.
