# scipy-talk

## Minimal Example

Get information about the files associated with the most recent release of a package.

```shell
./download-package.sh pandas
```

Analyze the contents of a specific artifact.

```shell
./summarize.sh \
    pandas.csv \
    pandas-1.4.2.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

Questions to be answered?

* what are the `n` largest files in this artifact?
* what is the total size (compressed and uncompressed) of this artifact?
* what file types (by extension) exist in this artifact? how much space do they take up?

Ideas for a file content linter:

* mixes of extensions for the same file type (e.g. `.yaml` and `.yml`)
* file types not expected to be found in a Python package

## References

* Python packaging guides: https://packaging.python.org/en/latest/guides/#
* PyPI APIs: https://warehouse.pypa.io/api-reference/index.html
