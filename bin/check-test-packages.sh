#!/bin/bash

# [description] test that the packages used in in unit tests
#               are valid, installable Python distributions

set -e -u -o pipefail

check_distro() {
    distro_file=${1}
    test_code=${2}
    echo ""
    echo "checking '${distro_file}'"
    pip uninstall --yes base-package problematic-package || true
    pip install "${distro_file}"
    python -c "${test_code}" || exit 1
    echo "success"
}

DISTRO_DIR="${1}"

pushd "${DISTRO_DIR}"

check_distro \
    'base-package-0.1.0.zip' \
    'from base_package.thing import do_stuff'

check_distro \
    'base-package-0.1.0.tar.gz' \
    'from base_package.thing import do_stuff'

check_distro \
    'problematic-package-0.1.0.zip' \
    'from problematic_package.question import SPONGEBOB_STR'

check_distro \
    'problematic-package-0.1.0.tar.gz' \
    'from problematic_package.question import SPONGEBOB_STR'

echo ""
echo "all test distributions are valid"
