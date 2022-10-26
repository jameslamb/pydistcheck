#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

mkdir -p ./smoke-tests

# wheel-only package
echo "  - catboost"
bin/full-run.sh \
    "catboost" \
    "${OUTPUT_DIR}/catboost"

# package where source distro is a .zip
echo "  - numpy"
bin/full-run.sh \
    "numpy" \
    "${OUTPUT_DIR}/numpy"

# package with so many files that `find -exec du -ch` has to batch results
echo "  - tensorflow"
bin/full-run.sh \
    "tensorflow" \
    "${OUTPUT_DIR}/tensorflow"

echo "done running smoke tests"
