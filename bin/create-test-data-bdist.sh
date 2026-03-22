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
    # pin the macOS API version minimum
    #
    # references:
    #
    #   - https://peps.python.org/pep-0425/
    #   - https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/#macos-platform-tag
    #   - https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/cross_development/Introduction/Introduction.html
    #
    export MACOSX_DEPLOYMENT_TARGET=12.0
else
    OS_NAME="linux"
    export PATH="/opt/python/cp311-cp311/bin:${PATH}"
fi

pip install --upgrade --no-cache-dir pip

clean_build_artifacts() {
    rm -rf ./baseballmetrics.egg-info
    rm -rf ./dist
    rm -rf ./dist-tmp
    rm -rf ./_skbuild
    rm -rf ./wheelhouse
    rm -f ./*.whl
}

pushd tests/data/baseballmetrics

clean_build_artifacts

if [[ $OS_NAME == "linux" ]]; then
    echo "building linux wheels"

    mkdir -p ./dist

    # debug build
    pip wheel \
        -w ./dist-tmp \
        --config-setting='cmake.build-type=Debug' \
        --config-setting='install.strip=false' \
        .

    auditwheel repair \
        -w ./dist \
        --plat='manylinux_2_28_x86_64' \
        ./dist-tmp/*.whl

    rm -rf ./dist-tmp

    # prefix distro name with 'debug-' (to clarify how it differs from the release builds)
    DEBUG_DISTRO="$(ls dist/*.whl)"
    mv \
        "${DEBUG_DISTRO}" \
        "${DEBUG_DISTRO/baseballmetrics-/debug-baseballmetrics-}"

    # release build
    pip wheel \
        -w ./dist-tmp \
        --config-setting='cmake.build-type=Release' \
        --config-setting='install.strip=true' \
        .

    auditwheel repair \
        -w ./dist \
        --plat='manylinux_2_28_x86_64' \
        ./dist-tmp/*.whl

    rm -rf ./dist-tmp

elif [[ $OS_NAME == "macos" ]]; then
    echo "building macOS wheels"

    # debug build
    pip wheel \
        -w ./dist \
        --config-setting='cmake.build-type=Debug' \
        --config-setting='install.strip=false' \
        .

    # prefix distro name with 'debug-' (to clarify how it differs from the release builds)
    DEBUG_DISTRO="$(ls dist/*.whl)"
    mv \
        "${DEBUG_DISTRO}" \
        "${DEBUG_DISTRO/baseballmetrics-/debug-baseballmetrics-}"

    # release build
    pip wheel \
        -w ./dist \
        --config-setting='cmake.build-type=Release' \
        --config-setting='install.strip=true' \
        .

    rm -rf ./tmp-dir
    mkdir -p ./tmp-dir
    unzip \
        -d ./tmp-dir \
        ./dist/debug-*.whl

    tar \
        -C ./tmp-dir \
        -c \
        --gzip \
        --strip-components=1 \
        -f dist/debug-baseballmetrics-0.1.0-macosx-wheel.tar.gz \
        .

    tar \
        -C ./tmp-dir \
        -c \
        --bzip2 \
        --strip-components=1 \
        -f dist/debug-baseballmetrics-0.1.0-macosx-wheel.tar.bz2 \
        .

    rm -rf ./tmp-dir

fi

mv ./dist/* ../

echo "done building wheels"
popd
