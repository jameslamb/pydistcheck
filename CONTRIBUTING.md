# contributing

## Building the package

This project uses `pipx` to run other Python-based CLIs.
Follow https://github.com/pypa/pipx#install-pipx to install it.

Then run the following.

```shell
make build install
```

## Releasing

1. Create a pull request with a version bump.

```shell
bin/create-release-pr '0.10.0'
```

2. Merge that PR.
3. navigate to https://github.com/jameslamb/pydistcheck/releases
4. edit the draft release there
    - remove any changelog items that are just "changed the version number" PRs
    - ensure that the tag that'll be created matches the version number, in the form `v{major}.{minor}.{patch}`
5. click "publish"
    - when that happens, CI jobs will run that automatically publish the package to PyPI.
6. Open another PR bumping the version

```shell
bin/create-version-bump-pr
```
