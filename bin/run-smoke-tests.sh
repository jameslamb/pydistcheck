#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

get-files() {
    pkg_name=$1
    rm -rf ./smoke-tests
    mkdir ./smoke-tests
    echo ""
    python bin/get-release-files.py \
        "${pkg_name}" \
        ./smoke-tests
}

# wheel-only package
get-files catboost
pydistcheck ./smoke-tests/*

# package where source distro is a .zip
get-files numpy
pydistcheck \
    --max-allowed-files 3000 \
    --max-allowed-size-uncompressed '150M' \
    ./smoke-tests/*

# package with so many files that `find -exec du -ch` has to batch results
get-files tensorflow
pydistcheck \
    --max-allowed-files 10000 \
    --max-allowed-size-compressed '300M' \
    --max-allowed-size-uncompressed '1G' \
    ./smoke-tests/*

# packages with lots of bundled non-Python code
get-files bokeh
pydistcheck ./smoke-tests/*

get-files Flask
pydistcheck ./smoke-tests/*

# package that isn't actually Python code
get-files cmake
pydistcheck \
    --ignore 'path-contains-spaces' \
    --max-allowed-files 4000 \
    --max-allowed-size-uncompressed '150M' \
    ./smoke-tests/*

# Python clients for other systems
get-files botocore
pydistcheck \
    --max-allowed-files 4000 \
    --max-allowed-size-uncompressed '150M' \
    ./smoke-tests/*

get-files kafka-python
pydistcheck ./smoke-tests/*

get-files kubernetes
pydistcheck ./smoke-tests/*

echo "done running smoke tests"
