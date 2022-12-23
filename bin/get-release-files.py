import os
import sys
from collections import defaultdict
from dataclasses import dataclass

import requests

PACKAGE_NAME = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
PYPI_URL = "https://pypi.org"

if os.path.isfile("out.json"):
    raise RuntimeError("file './out.json' exists, not recreating it.")

print(f"Getting PyPI details for package '{PACKAGE_NAME}'")
res = requests.get(url=f"{PYPI_URL}/pypi/{PACKAGE_NAME}/json")
res.raise_for_status()
release_info = res.json()

latest_version = release_info["info"]["version"]
files = release_info["releases"][latest_version]


@dataclass
class _ReleaseFile:
    filename: str
    package_type: str
    url: str


files_by_type = defaultdict(list)
for file_info in files:
    files_by_type[file_info["packagetype"]].append(
        _ReleaseFile(
            filename=file_info["filename"],
            package_type=file_info["packagetype"],
            url=file_info["url"],
        )
    )

print(f"Found the following file types for '{PACKAGE_NAME}=={latest_version}':")
for file_type, release_files in files_by_type.items():
    print(f"  * {file_type} ({len(release_files)})")


for file_type in files_by_type.keys():
    sample_release = files_by_type[file_type][0]
    output_file = os.path.join(OUTPUT_DIR, sample_release.filename)
    print(f"Downloading '{sample_release.filename}'")
    res = requests.get(url=sample_release.url, headers={"Accept": "application/octet-stream"})
    res.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(res.content)

print(f"Done downloading files into '{OUTPUT_DIR}'")
