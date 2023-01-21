#!/bin/bash

# [description]
#
#     generate test built distributions
#
# [references]
#
#     https://github.com/RalfG/python-wheels-manylinux-build/tree/9b1fc896a2182325489b317042594f9fd9c41a02

set -e -u -o pipefail

if [[ $OSTYPE == 'darwin'* ]]; then
  OS_NAME="macos"
else
  OS_NAME="linux"
fi

clean_build_artifacts() {
    rm -rf ./baseballmetrics.egg-info
    rm -rf ./dist
    rm -rf ./_skbuild
    rm -rf ./wheelhouse
    rm -f ./*.whl
}

build_linux_wheel() {
    PIP="/opt/python/${1}/bin/pip"
    ${PIP} install --upgrade --no-cache-dir pip
    ${PIP} wheel \
        --config-setting='cmake.build-type=${2}' \
        -w ./dist \
        .
}

pushd tests/data/baseballmetrics
    clean_build_artifacts
    if [[ $OS_NAME == "linux" ]]; then
      echo "building linux wheels"
      build_linux_wheel 'cp311-cp311' 'Debug'
      mv \
          ./dist/baseballmetrics-0.1.0-py3-none-manylinux_2_28_x86_64.whl \
          ./dist/debug-baseballmetrics-0.1.0-py3-none-manylinux_2_28_x86_64.whl
      build_linux_wheel 'cp311-cp311' 'Release'
      auditwheel repair \
          -w ./dist \
          --plat='manylinux_2_28_x86_64' \
          ./dist/*.whl
    elif [[ $OS_NAME == "macos" ]]; then
      echo "building macOS wheels"
      pip wheel \
          -w ./dist \
          --config-setting='cmake.build-type=Debug' \
          .
      mv \
          ./dist/baseballmetrics-0.1.0-py3-none-macosx_*.whl \
          ./dist/debug-baseballmetrics-0.1.0-py3-none-macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl

      pip wheel -w ./dist .
      mv \
        ./dist/baseballmetrics-0.1.0-py3-none-macosx_*.whl \
        ./dist/baseballmetrics-0.1.0-py3-none-macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl
    fi
    mv \
        ./dist/*.whl \
        ../
    echo "done building wheels"
popd
