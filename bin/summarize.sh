#!/bin/bash

# [description]
#    Given a Python package tarball, summarize its contents.
#        - total size
#        - number of files
#        - longest filepath names
#        - largest files
#        - total size of files, grouped by file extension

set -e -u -o pipefail

ARTIFACT_NAME="${1}"
CSV_FILE="${2}"
OUTPUT_DIR="${3}"
TEMP_PATH="${OUTPUT_DIR}/tmp-dir"

FILE_EXTENSION=$(
    echo "${ARTIFACT_NAME}" \
    | grep \
        -o \
        -E "\.*[tar]*\.[a-zA-Z0-9]+$"
)
TEMP_FILE_NAME="package${FILE_EXTENSION}"

mkdir -p "${TEMP_PATH}"
cp "${ARTIFACT_NAME}" "${TEMP_PATH}/${TEMP_FILE_NAME}"

pushd "${TEMP_PATH}"

echo "checking compressed size..."
du --si ./"${TEMP_FILE_NAME}"

echo "decompressing..."
if [[ "${FILE_EXTENSION}" == ".tar.gz" ]]; then
    tar -xzf ./"${TEMP_FILE_NAME}"
elif [[ "${FILE_EXTENSION}" == ".zip" || "${FILE_EXTENSION}" == ".whl" ]]; then
    unzip -q ./"${TEMP_FILE_NAME}"
else
    echo "did not recognize extension '${FILE_EXTENSION}'"
    exit 1
fi

rm ./"${TEMP_FILE_NAME}"

echo "checking decompressed size..."
du -sh .

echo "summarizing contents"
# references:
# - https://unix.stackexchange.com/a/41552
ALL_FILE_EXTENSIONS=$(
    find \
        "${TEMP_PATH}" \
        -type f \
    | grep \
        -o \
        -E "\.[a-zA-Z0-9]+$" \
    | sort -u
)
echo "Found the following file extensions"

echo "Summarizing file sizes by extension"
echo "extension,size" > "${CSV_FILE}"
for extension in ${ALL_FILE_EXTENSIONS}; do
    echo "  * ${extension}"
    SIZE=$(
        find \
            "${TEMP_PATH}" \
            -type f \
            -name "*${extension}" \
            -exec du -ch {} + \
        | grep -E 'total$' \
        | grep \
            -o \
            -E '[0-9.]+[A-Z]*'
    )
    echo "${extension},${SIZE}" >> "${CSV_FILE}"
done

echo "  * (no extension)"
SIZE=$(
    find \
        "${TEMP_PATH}" \
        -type f \
        ! -name '*.*' \
        -exec du -ch {} + \
    | grep -E 'total$' \
    | grep \
        -o \
        -E '[0-9.]+[A-Z]+'
)
echo "no-extension,${SIZE}" >> "${CSV_FILE}"

echo "done summarizing sizes"
