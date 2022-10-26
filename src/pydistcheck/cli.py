"""
CLI entrypoints
"""

import os
import sys
from typing import Dict, List, Union

import click

from pydistcheck._compat import tomllib
from pydistcheck.checks import (
    _DistroTooLargeCompressedCheck,
    _DistroTooLargeUnCompressedCheck,
    _FileCountCheck,
)
from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.inspect import inspect_distribution
from pydistcheck.utils import _FileSize


@click.command()
@click.argument(
    "filename",
    type=click.Path(exists=True),
)
@click.option(
    "--inspect",
    is_flag=True,
    show_default=False,
    default=False,
    help="print diagnostic information about the distribution",
)
@click.option(
    "--max-allowed-files",
    default=2000,
    type=int,
    help="maximum number of files allowed in the distribution",
)
@click.option(
    "--max-allowed-size-compressed",
    default="50M",
    type=str,
    help=(
        "maximum allowed compressed size, a string like '1.5M' indicating"
        " '1.5 megabytes'. Supported units:\n"
        "  - B = bytes\n"
        "  - K = kilobytes\n"
        "  - M = megabytes\n"
        "  - G = gigabytes"
    ),
)
@click.option(
    "--max-allowed-size-uncompressed",
    default="75M",
    type=str,
    help=(
        "maximum allowed uncompressed size, a string like '1.5M' indicating"
        " '1.5 megabytes'. Supported units:\n"
        "  - B = bytes\n"
        "  - K = kilobytes\n"
        "  - M = megabytes\n"
        "  - G = gigabytes"
    ),
)
def check(
    filename: str,
    inspect: bool,
    max_allowed_files: int,
    max_allowed_size_compressed: str,
    max_allowed_size_uncompressed: str,
) -> None:
    """
    Run the contents of a distribution through a set of checks, and raise
    errors if those are not met.
    """
    print("running pydistcheck")
    print(click.format_filename(filename))

    tool_options: Dict[str, Union[int, str]] = {}
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            config_dict = tomllib.load(f)
            tool_options = config_dict.get("tool", {}).get("pydistcheck", {})

    print("pyproject options")
    print(tool_options)

    if inspect:
        inspect_distribution(filepath=click.format_filename(filename))

    checks = [
        _DistroTooLargeCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=max_allowed_size_compressed
            ).total_size_bytes
        ),
        _DistroTooLargeUnCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=max_allowed_size_uncompressed
            ).total_size_bytes
        ),
        _FileCountCheck(max_allowed_files=max_allowed_files),
    ]

    summary = _DistributionSummary.from_file(filename=click.format_filename(filename))
    errors: List[str] = []
    for this_check in checks:
        errors += this_check(distro_summary=summary)

    for i, error_msg in enumerate(errors):
        print(f"{i + 1}. {error_msg}")

    print(f"errors found while checking: {len(errors)}")
    sys.exit(len(errors))
