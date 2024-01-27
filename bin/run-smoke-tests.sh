#!/bin/bash

set -e -u -o pipefail

echo "running smoke tests"

get-files() {
    pkg_name=$1
    rm -rf ./smoke-tests
    mkdir ./smoke-tests
    echo ""
    python bin/get-release-files.py \
        "${pkg_name}" \
        ./smoke-tests
}

# wheel-only packages
get-files catboost
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols,mixed-file-extensions,too-many-files,unexpected-files' \
    --max-allowed-size-compressed '100M' \
    --max-allowed-size-uncompressed '0.5G' \
    ./smoke-tests/*

get-files psycopg2-binary
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    ./smoke-tests/*

# package where source distro is a .zip
get-files numpy
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols,mixed-file-extensions,path-contains-spaces,unexpected-files' \
    --max-allowed-files 7500 \
    --max-allowed-size-uncompressed '150M' \
    ./smoke-tests/*

# package with so many files that `find -exec du -ch` has to batch results
get-files tensorflow
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols,mixed-file-extensions' \
    --max-allowed-files 15000 \
    --max-allowed-size-compressed '500M' \
    --max-allowed-size-uncompressed '1.5G' \
    ./smoke-tests/*

# packages with lots of bundled non-Python code
get-files bokeh
pydistcheck ./smoke-tests/*

get-files Flask
pydistcheck \
    --ignore 'unexpected-files' \
    ./smoke-tests/*

# package that isn't actually Python code
get-files cmake
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols,mixed-file-extensions,path-contains-spaces,unexpected-files' \
    --max-allowed-files 4000 \
    --max-allowed-size-uncompressed '150M' \
    ./smoke-tests/*

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
pydistcheck \
    --ignore 'mixed-file-extensions,unexpected-files' \
    ./smoke-tests/*

get-files astropy
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols,mixed-file-extensions,unexpected-files' \
    ./smoke-tests/*

get-files datatable
pydistcheck \
    --ignore 'compiled-objects-have-debug-symbols' \
    --max-allowed-size-compressed '100M' \
    --max-allowed-size-uncompressed '100M' \
    ./smoke-tests/*

get-files gensim
pydistcheck \
    ./smoke-tests/*

get-files opencv-python
pydistcheck \
    --ignore 'mixed-file-extensions,unexpected-files' \
    --max-allowed-files 7500 \
    --max-allowed-size-compressed '90M' \
    --max-allowed-size-uncompressed '200M' \
    ./smoke-tests/*

get-files pandas
pydistcheck ./smoke-tests/*

get-files Pillow
pydistcheck \
    ./smoke-tests/*

get-files pytest
pydistcheck \
    --ignore 'mixed-file-extensions,unexpected-files' \
    ./smoke-tests/*

get-files scikit-learn
pydistcheck \
    --ignore 'mixed-file-extensions,unexpected-files' \
    ./smoke-tests/*

get-files Shapely
pydistcheck \
    ./smoke-tests/*

get-files spacy
pydistcheck \
    ./smoke-tests/*

echo "done running smoke tests"
