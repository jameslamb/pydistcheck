#!/bin/bash

# [description] test that the packages used in in unit tests
#               are valid, installable Python distributions

set -e -u -o pipefail

if [[ $OSTYPE =~ [Dd]arwin.* ]]; then
    OS_NAME="macos"
else
    OS_NAME="linux"
fi

check_distro() {
    local distro_file=${1}
    local test_code=${2}
    echo ""
    echo "checking '${distro_file}'"
    pip uninstall -qq --yes \
        baseballmetrics \
        base-package \
        problematic-package
    pip install -qq "${distro_file}"
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

# NOTE: problematic-package doesn't work on macOS because of
#       the problems like mixed case in filepaths, special characters, etc.
if [[ $OS_NAME == "linux" ]]; then

    check_distro \
        'problematic-package-0.1.0.zip' \
        'from problematic_package.question import SPONGEBOB_STR'

    check_distro \
        'problematic-package-0.1.0.tar.gz' \
        'from problematic_package.question import SPONGEBOB_STR'

    check_distro \
        'baseballmetrics-0.1.0-py3-none-manylinux_2_28_x86_64.manylinux_2_5_x86_64.manylinux1_x86_64.whl' \
        'from baseballmetrics.metrics import batting_average; assert batting_average(2, 4) == 0.5'
else

    check_distro \
        'baseballmetrics-0.1.0-py3-none-macosx_10_15_x86_64.macosx_11_6_x86_64.macosx_12_5_x86_64.whl' \
        'from baseballmetrics.metrics import batting_average; assert batting_average(2, 4) == 0.5'

fi

echo ""
echo "all test distributions are valid"
