#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

rm -rf ./smoke-tests
mkdir -p ./smoke-tests

get-files() {
    pkg_name=$1
    echo ""
    python bin/get-release-files.py \
        "${pkg_name}" \
        ./smoke-tests
}

# wheel-only package
get-files catboost

# package where source distro is a .zip
get-files numpy

# package with so many files that `find -exec du -ch` has to batch results
get-files tensorflow

# package with lots of bundled non-Python code
get-files bokeh
get-files Flask

# package that isn't actually Python code
get-files cmake

# Python clients for other systems
get-files botocore
get-files kafka-python
get-files kubernetes

pydistcheck \
    --ignore 'path-contains-spaces' \
    --max-allowed-files 8750 \
    --max-allowed-size-compressed '500M' \
    --max-allowed-size-uncompressed '1G' \
    ./smoke-tests/*

echo "done running smoke tests"
