#!/bin/bash

# [description]
#
#   generate test conda packages
#
# [references]
#
#   - https://conda.io/projects/conda/en/latest/user-guide/configuration/use-condarc.html
#   - https://github.com/conda/conda-build/blame/main/docs/source/resources/package-spec.rst
#   - https://github.com/conda/conda-docs/issues/796
#   - https://docs.anaconda.com/free/anacondaorg/user-guide/packages/manage-packages/#conda-compression-format

CHANNEL="${1}"

set -Eeuox pipefail

REPO_ROOT="${PWD}"
TEST_DATA_DIR="${PWD}/tests/data"

new_build_dir() {
    rm -rf ./conda-build
    mkdir ./conda-build
    cd ./conda-build
}

conda_build() {
    cd "${REPO_ROOT}"
    new_build_dir
    conda build \
        --no-anaconda-upload \
        --no-test \
        --no-verify \
        --old-build-string \
        "${1}"
    rm -f ./build_env_setup.sh
}

# start with .tar.bz2 packages
conda config --set conda_build.pkg_format 1

#----------------------------#
#- baseballmetrics*.tar.bz2 -#
#----------------------------#
conda_build ../tests/data/conda-recipes/baseballmetrics

#----------------------------------#
#- debug-baseballmetrics*.tar.bz2 -#
#----------------------------------#
conda_build ../tests/data/conda-recipes/debug-baseballmetrics

# get packages
cp \
    $(conda info --base)/conda-bld/${CHANNEL}/baseballmetrics-0.1.0-0.tar.bz2 \
    "${TEST_DATA_DIR}/${CHANNEL}-baseballmetrics-0.1.0-0.tar.bz2"

cp \
    $(conda info --base)/conda-bld/${CHANNEL}/debug-baseballmetrics-0.1.0-0.tar.bz2 \
    "${TEST_DATA_DIR}/${CHANNEL}-debug-baseballmetrics-0.1.0-0.tar.bz2"

# clean up
cd "${REPO_ROOT}"
rm -rf ./conda-build
