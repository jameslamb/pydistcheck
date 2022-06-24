#!/bin/bash

set -e -u -o pipefail

PACKAGE_NAME="${1}"
OUTPUT_DIR="${2}"
LINTER_BIN_DIR="$(pwd)/bin"

if [ -d "${OUTPUT_DIR}" ]; then
    echo "ERROR: directory '${OUTPUT_DIR}' already exists"
    exit 1
else
    echo "creating directory '${OUTPUT_DIR}'"
    mkdir -p "${OUTPUT_DIR}"
fi

ARTIFACTS_CSV="${OUTPUT_DIR}/artifacts.csv"
RELEASE_JSON_FILE="${OUTPUT_DIR}/release-info.json"
SOURCE_SIZES_CSV="${OUTPUT_DIR}/source-sizes.csv"
WHEEL_SIZES_CSV="${OUTPUT_DIR}/wheel-sizes.csv"

bin/get-release-info.sh \
    "${PACKAGE_NAME}" \
    "${RELEASE_JSON_FILE}" \
    "${ARTIFACTS_CSV}"

echo "searching for source artifact name"
SOURCE_FILE=$(
    cat "${ARTIFACTS_CSV}" \
    | grep -E '\.tar\.gz,|\.zip,' \
    | head -1 \
    | awk -F"," '{print $1}' \
    || echo ""
)
if [[ "${SOURCE_FILE}" == "" ]]; then
    echo "[WARNING] no source artifacts (.tar.gz or .zip) found"
else
    echo "source artifact: '${SOURCE_FILE}'"

    bin/download-package.sh \
        "${ARTIFACTS_CSV}" \
        "${SOURCE_FILE}" \
        "${OUTPUT_DIR}"

    bin/summarize.sh \
        "${OUTPUT_DIR}/${SOURCE_FILE}" \
        "${SOURCE_SIZES_CSV}" \
        "${OUTPUT_DIR}" \
        "${LINTER_BIN_DIR}"

    python bin/summarize-sizes.py \
        "${SOURCE_SIZES_CSV}"
fi

echo "searching for a wheel"
WHEEL_FILE=$(
    cat "${ARTIFACTS_CSV}" \
    | grep -E '.*any.*\.whl,' \
    | head -1 \
    | awk -F"," '{print $1}' \
    || echo ""
)
if [[ "${WHEEL_FILE}" == "" ]]; then
    echo "[WARNING] no wheels (.whl) found"
else
    echo "wheel: '${WHEEL_FILE}'"

    bin/download-package.sh \
        "${ARTIFACTS_CSV}" \
        "${WHEEL_FILE}" \
        "${OUTPUT_DIR}"

    bin/summarize.sh \
        "${OUTPUT_DIR}/${WHEEL_FILE}" \
        "${WHEEL_SIZES_CSV}" \
        "${OUTPUT_DIR}" \
        "${LINTER_BIN_DIR}"

    python bin/summarize-sizes.py \
        "${WHEEL_SIZES_CSV}"
fi
