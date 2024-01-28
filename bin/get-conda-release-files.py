import os
import sys
from collections import defaultdict
from dataclasses import dataclass

import requests

PACKAGE_NAME = sys.argv[1]
OUTPUT_DIR = sys.argv[2]
BASE_URL = "https://api.anaconda.org/package/conda-forge"

print(f"Getting conda-forge details for package '{PACKAGE_NAME}'")
res = requests.get(url=f"{BASE_URL}/{PACKAGE_NAME}")
res.raise_for_status()
release_info = res.json()

latest_version = release_info["versions"][-1]
files = [
    f for f in release_info["files"]
    if f["version"] == latest_version
]


@dataclass
class _ReleaseFile:
    filename: str
    package_type: str
    url: str


files_by_type = defaultdict(list)
for file_info in files:
    pkg_type = file_info["attrs"]["target-triplet"]
    url = file_info["download_url"]
    if url.startswith("//"):
        url = f"https:{url}"
    files_by_type[pkg_type].append(
        _ReleaseFile(
            filename=file_info["basename"].replace("/", "-"),
            package_type=pkg_type,
            url=url,
        )
    )

print(f"Found the following file types for '{PACKAGE_NAME}=={latest_version}':")
for file_type, release_files in files_by_type.items():
    print(f"  * {file_type} ({len(release_files)})")


for file_type in files_by_type:
    sample_release = files_by_type[file_type][0]
    output_file = os.path.join(OUTPUT_DIR, sample_release.filename)
    print(f"Downloading '{sample_release.filename}'")
    res = requests.get(url=sample_release.url, headers={"Accept": "application/octet-stream"})
    res.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(res.content)

print(f"Done downloading files into '{OUTPUT_DIR}'")
