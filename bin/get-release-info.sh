#!/bin/bash

set -e -u -o pipefail

PACKAGE_NAME="${1}"
RELEASE_INFO_FILE="${2}"
CSV_FILE="${3}"
PYPI_URL="https://pypi.org"

if [ -f ./out.json ]; then
    echo "file './out.json' exists, not recreating it"
    exit 0
else
    echo "downloading PyPI details for package '${PACKAGE_NAME}'"
    curl \
        "${PYPI_URL}/pypi/${PACKAGE_NAME}/json" \
        -o "${RELEASE_INFO_FILE}"
fi

LATEST_VERSION=$(
    jq -r '."info"."version"' "${RELEASE_INFO_FILE}"
)

echo "latest version of '${PACKAGE_NAME}': ${LATEST_VERSION}"
echo "this release contains the following files:"
echo "file_name,size_bytes,download_url" > "${CSV_FILE}"

# NOTE: subsetting to specific fields in the jq expression below is important
#       to minimize parsing issues caused by characters like '<', '>', and newlines
for file_info in $(
        jq \
            -r \
            --arg version "${LATEST_VERSION}" \
            '."releases"[$version] | keys[] as $k | "\(.[$k] | {filename, size, url})"' \
            "${RELEASE_INFO_FILE}"
    );
do
    echo "----"
    file_name=$(
        echo -n "${file_info}" \
        | jq -r '."filename"'
    )
    file_size_bytes=$(
        echo "${file_info}" \
        | jq -r '."size"'
    )
    download_url=$(
        echo "${file_info}" \
        | jq -r '."url"'
    )
    echo "  * (${file_size_bytes}) ${file_name}"
    echo "${file_name},${file_size_bytes},${download_url}" >> "${CSV_FILE}"
done
