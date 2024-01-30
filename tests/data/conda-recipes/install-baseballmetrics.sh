#!/bin/bash

python -m pip install \
    --no-deps \
    -v \
    --config-settings='cmake.build-type=Release' \
    "${BASEBALLMETRICS_SOURCE_DIR}"
