## end-to-end

```shell
bin/full-run.sh \
    s3transfer \
    $(pwd)/s3transfer
```

## numpy

source distribution

```shell
bin/get-release-info.sh \
    numpy \
    $(pwd)/numpy-release-info.json

bin/download-package.sh \
    ./numpy.csv \
    numpy-1.22.4.zip

bin/summarize.sh \
    ./numpy-1.22.4.zip \
    $(pwd)/numpy-source-sizes.csv

python bin/summarize-sizes.py \
    $(pwd)/numpy-source-sizes.csv
```

wheel

```shell
bin/download-package.sh \
    ./numpy.csv \
    numpy-1.22.4-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl

bin/summarize.sh \
    ./numpy-1.22.4-cp39-cp39-manylinux_2_17_aarch64.manylinux2014_aarch64.whl \
    $(pwd)/numpy-wheel-sizes.csv

python bin/summarize-sizes.py \
    $(pwd)/numpy-wheel-sizes.csv
```

## prefect

```shell
./download-package.sh prefect

./summarize.sh \
    prefect.csv \
    prefect-1.2.2.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

## psycopg2

```shell
bin/get-release-info.sh \
    psycopg2 \
    $(pwd)/psycopg2-release-info.json

bin/download-package.sh \
    ./psycopg2.csv \
    psycopg2-2.9.3.tar.gz

bin/summarize.sh \
    ./psycopg2-2.9.3.tar.gz \
    $(pwd)/psycopg2-source-sizes.csv

python bin/summarize-sizes.py \
    $(pwd)/psycopg2-source-sizes.csv
```

## pyarrow

```shell
./download-package.sh pyarrow

./summarize.sh \
    pyarrow.csv \
    pyarrow-8.0.0.tar.gz

python ./summarize-sizes.py \
    ./tmp-dir/sizes.csv
```

## snowflake-connector-python

```shell
mkdir -p ./snowflake-connector-python

bin/get-release-info.sh \
    snowflake-connector-python \
    $(pwd)/snowflake-connector-python/release-info.json

bin/download-package.sh \
    ./snowflake-connector-python.csv \
    snowflake-connector-python-2.7.8.tar.gz

bin/summarize.sh \
    ./snowflake-connector-python-2.7.8.tar.gz \
    $(pwd)/snowflake-connector-python/sizes.csv

python bin/summarize-sizes.py \
    $(pwd)/snowflake-connector-python/sizes.csv
```
