#!/bin/bash

pip wheel \
    -w ./dist \
    --config-setting='cmake.build-type=Release' \
    "${BASEBALLMETRICS_SOURCE_DIR}"

pip install \
    --no-deps \
    -v \
    ./dist/*.whl
