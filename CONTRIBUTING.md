# contributing

## Building the package

This project uses `pipx` to run other Python-based CLIs.
Follow https://github.com/pypa/pipx#install-pipx to install it.

Then run the following.

```shell
make build install
```

## Releasing

Open a pull request changing `VERSION.txt` to the desired version.

After merging the pull request, create a GitHub release.

1. navigate to https://github.com/jameslamb/pydistcheck/releases
2. edit the draft release
3. click "publish"

When that happens, CI jobs will run that automatically publish the package to PyPI.

Open another pull request adding `.99` to the version in `VERSION.txt`.
