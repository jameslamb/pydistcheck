#!/bin/bash

set -e -u -o pipefail

PACKAGE_DIR="${1}"

echo "--- sdist-only checks ---"

gunzip -t "${PACKAGE_DIR}"/*.tar.gz

# pyroma can be added again once it can handle PEP 639 license metadata
# https://github.com/regebro/pyroma/issues/93 is resolved but it still fails with
# "malformed field 'license-expression'"
#
# pyroma --min=10 dist/*.tar.gz

# using command-line arguments to avoid having a '[tools.pydistcheck]'
# table in this repo's pyproject.toml (which might confuse tests)
#
# explanations:
#
#   - pyproject.toml is needed for repackagers like conda-forge
#   - licenses need to be included to respect license terms
#
pydistcheck \
    --inspect \
    --expected-files 'pydistcheck-*/LICENSE' \
    --expected-files 'pydistcheck-*/LICENSES/DELOCATE_LICENSE' \
    --expected-files 'pydistcheck-*/pyproject.toml' \
    --max-allowed-files 30 \
    "${PACKAGE_DIR}"/*.tar.gz

echo "--- wheel-only checks ---"

zip -T "${PACKAGE_DIR}"/*.whl
check-wheel-contents "${PACKAGE_DIR}"/*.whl

pydistcheck \
    --inspect \
    --expected-directories '!pydistcheck/tests' \
    --expected-files 'pydistcheck-*/LICENSE' \
    --expected-files 'pydistcheck-*/LICENSES/DELOCATE_LICENSE' \
    --expected-files '!pydistcheck-*/pyproject.toml' \
    --max-allowed-files 17 \
    "${PACKAGE_DIR}"/*.whl

echo "--- sdist-and-wheel checks ---"

twine check --strict "${PACKAGE_DIR}"/*

echo "done checking distributions"
