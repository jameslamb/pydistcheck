#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

get-files() {
    local pkg_name=$1
    rm -rf ./smoke-tests
    mkdir -p ./smoke-tests
    echo ""
    python bin/get-pypi-files.py \
        "${pkg_name}" \
        ./smoke-tests
}

get-conda-forge-files() {
    local pkg_name=$1
    mkdir -p ./smoke-tests
    echo ""
    python bin/get-conda-release-files.py \
        "${pkg_name}" \
        'conda-forge' \
        ./smoke-tests
}

# conda package where conda-forge only has the old .tar.bz2 format
get-conda-forge-files librmm
get-conda-forge-files rmm
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

# wheel-only packages
get-files catboost
get-conda-forge-files catboost
shared_args=(
    --ignore=compiled-objects-have-debug-symbols
    --ignore=mixed-file-extensions
    --ignore=too-many-files
    --max-allowed-size-compressed=100M
    --max-allowed-size-uncompressed='0.5G'
)
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.conda
pydistcheck \
    "${shared_args[@]}" \
    --expected-directories='*/.github' \
    --expected-files='*/.gitignore' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

get-files psycopg2-binary
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

# package where source distro is a .zip
get-files numpy
get-conda-forge-files numpy
shared_args=(
    --ignore=compiled-objects-have-debug-symbols
    --ignore=mixed-file-extensions
    --ignore=path-contains-spaces
    --max-allowed-files=7500
    --max-allowed-size-uncompressed=150M
)
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.conda
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl
pydistcheck \
    "${shared_args[@]}" \
    --expected-files '*/azure-pipelines.yml' \
    --expected-files '*/.cirrus.star' \
    --expected-files '*/.codecov.yml' \
    --expected-files '*/.gitignore' \
    ./smoke-tests/*.tar.gz

# package with so many files that `find -exec du -ch` has to batch results
get-files tensorflow
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    --ignore 'mixed-file-extensions' \
    --max-allowed-files 15000 \
    --max-allowed-size-compressed '500M' \
    --max-allowed-size-uncompressed '1.5G' \
    ./smoke-tests/*

# packages with lots of bundled non-Python code
get-files bokeh
pydistcheck ./smoke-tests/*

get-files Flask
pydistcheck \
    ./smoke-tests/*.whl

pydistcheck \
    --expected-files '*/.gitignore' \
    ./smoke-tests/*.tar.gz

# package that isn't actually Python code
get-files cmake
shared_args=(
    --ignore=compiled-objects-have-debug-symbols
    --ignore=mixed-file-extensions
    --ignore=path-contains-spaces
    --max-allowed-files=4000
    --max-allowed-size-uncompressed=150M
)
pydistcheck \
    "${shared_args[@]}" \
    --expected-files '*/.gitignore' \
    --expected-files '*/.readthedocs.yaml' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

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

# other complex projects that do custom packaging stuff
get-files apache-airflow
shared_args=(
    --ignore=mixed-file-extensions
)
pydistcheck \
    "${shared_args[@]}" \
    --expected-files '*/.gitignore' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

get-files astropy
shared_args=(
    --expected-files='*/.gitignore'
    --ignore=compiled-objects-have-debug-symbols
    --ignore=mixed-file-extensions
)
pydistcheck \
    "${shared_args[@]}" \
    --expected-directories '*/.circleci' \
    --expected-directories '*/.github' \
    --expected-files '*/codecov.yml' \
    --expected-files '*/.readthedocs.yaml' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

get-files datatable
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    --max-allowed-size-compressed '100M' \
    --max-allowed-size-uncompressed '100M' \
    ./smoke-tests/*

get-files gensim
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

get-files opencv-python
shared_args=(
    --ignore=compiled-objects-have-debug-symbols
    --ignore=mixed-file-extensions
    --max-allowed-files=8000
    --max-allowed-size-compressed=95M
    --max-allowed-size-uncompressed=200M
)
pydistcheck \
    "${shared_args[@]}" \
    --expected-directories '*/.github' \
    --expected-files '*/.gitignore' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

get-files pandas
pydistcheck ./smoke-tests/*

get-files Pillow
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

get-files pytest
shared_args=(
    --ignore=mixed-file-extensions
)
pydistcheck \
    "${shared_args[@]}" \
    --expected-directories '*/.github' \
    --expected-files '*/codecov.yml' \
    --expected-files '*/.gitignore' \
    ./smoke-tests/*.tar.gz
pydistcheck \
    "${shared_args[@]}" \
    ./smoke-tests/*.whl

get-files scikit-learn
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    --ignore 'mixed-file-extensions' \
    ./smoke-tests/*

get-files Shapely
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

get-files spacy
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

echo "done running smoke tests"
