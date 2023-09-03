#!/bin/bash

#set -e -u -o pipefail

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
    ./smoke-tests/*

get-files psycopg2-binary
pydistcheck \
    ./smoke-tests/*

# package where source distro is a .zip
get-files numpy
pydistcheck \
    ./smoke-tests/*

# package with so many files that `find -exec du -ch` has to batch results
get-files tensorflow
pydistcheck \
    ./smoke-tests/*

# packages with lots of bundled non-Python code
get-files bokeh
pydistcheck ./smoke-tests/*

get-files Flask
pydistcheck \
    ./smoke-tests/*

# package that isn't actually Python code
get-files cmake
pydistcheck \
    ./smoke-tests/*

# Python clients for other systems
get-files botocore
pydistcheck \
    ./smoke-tests/*

get-files kafka-python
pydistcheck ./smoke-tests/*

get-files kubernetes
pydistcheck ./smoke-tests/*

# other complex projects that do custom packaging stuff
get-files apache-airflow
pydistcheck \
    ./smoke-tests/*

get-files astropy
pydistcheck \
    ./smoke-tests/*

get-files datatable
pydistcheck \
    ./smoke-tests/*

get-files gensim
pydistcheck \
    ./smoke-tests/*

get-files opencv-python
pydistcheck \
    ./smoke-tests/*

get-files pandas
pydistcheck ./smoke-tests/*

get-files Pillow
pydistcheck \
    ./smoke-tests/*

get-files pytest
pydistcheck \
    ./smoke-tests/*

get-files scikit-learn
pydistcheck \
    ./smoke-tests/*

get-files Shapely
pydistcheck \
    ./smoke-tests/*

get-files spacy
pydistcheck \
    ./smoke-tests/*

echo "done running smoke tests"

exit 1
