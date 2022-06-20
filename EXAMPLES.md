
```shell
./download-package.sh numpy

./summarize.sh \
    numpy.csv \
    numpy-1.22.4.zip

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

```shell
./download-package.sh prefect

./summarize.sh \
    prefect.csv \
    prefect-1.2.2.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

```shell
./download-package.sh pyarrow

./summarize.sh \
    pyarrow.csv \
    pyarrow-8.0.0.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

```shell
./download-package.sh snowflake-connector-python

./summarize.sh \
    snowflake-connector-python.csv \
    snowflake-connector-python-2.7.8.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```
