#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

rm -rf ./smoke-tests
mkdir -p ./smoke-tests

get-files() {
    pkg_name=$1
    python bin/get-release-files.py \
        "${pkg_name}" \
        ./smoke-tests
}

# wheel-only package
get-files catboost

# package where source distro is a .zip
get-files numpy

# package with so many files that `find -exec du -ch` has to batch results
get-files numpy

pydistcheck \
    --inspect \
    --max-allowed-files 2500 \
    --max-allowed-size-compressed '75M' \
    --max-allowed-size-uncompressed '100M' \
    ./smoke-tests/*

echo "done running smoke tests"
