#!/bin/bash

set -e -u -o pipefail

INFO_CSV="${1}"
ARTIFACT_NAME="${2}"

DOWNLOAD_URL=$(
    cat "${INFO_CSV}" \
    | grep "^${ARTIFACT_NAME}," \
    | awk -F"," '{print $3}'
)

if [ -f "${ARTIFACT_NAME}" ]; then
    echo "file '${ARTIFACT_NAME}' exists, not re-downloading it"
    exit 0
fi

curl \
    -o "${ARTIFACT_NAME}" \
    ${DOWNLOAD_URL}
