#!/bin/bash

# [description]
#
#     generate test built distributions
#
# [references]
#
#     https://github.com/RalfG/python-wheels-manylinux-build/tree/9b1fc896a2182325489b317042594f9fd9c41a02

set -e -u -o pipefail

clean_build_artifacts() {
    rm -rf ./baseballmetrics.egg-info
    rm -rf ./dist
    rm -rf ./_skbuild
    rm -rf ./wheelhouse
    rm -f ./*.whl
}

build_wheel() {
    PIP="/opt/python/${1}/bin/pip"
    PLAT="manylinux_2_28_x86_64"
    ${PIP} install --upgrade --no-cache-dir pip
    ${PIP} wheel \
        --config-setting='cmake.build-type=Debug' \
        --config-setting='logging.level=DEBUG' \
        -w ./dist \
        .
    # auditwheel repair \
    #     -w ./dist \
    #     --plat=${PLAT} \
    #     ./dist/*.whl 
}

pushd tests/data/baseballmetrics
    clean_build_artifacts
    build_wheel 'cp311-cp311'
    mv \
        ./dist/*.whl \
        ../
popd
