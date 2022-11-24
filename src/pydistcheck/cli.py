"""
CLI entrypoints
"""

import sys
from typing import List

import click

from pydistcheck.checks import (
    _DistroTooLargeCompressedCheck,
    _DistroTooLargeUnCompressedCheck,
    _FileCountCheck,
    _FilesOnlyDifferByCaseCheck,
    _NonAsciiCharacterCheck,
    _SpacesInPathCheck,
)
from pydistcheck.config import _Config
from pydistcheck.distribution_summary import _DistributionSummary
from pydistcheck.inspect import inspect_distribution
from pydistcheck.utils import _FileSize


@click.command()
@click.argument(
    "filepaths",
    type=click.Path(exists=True),
    nargs=-1,
)
@click.option(
    "--inspect",
    is_flag=True,
    show_default=False,
    default=_Config.inspect,
    help="print diagnostic information about the distribution",
)
@click.option(
    "--max-allowed-files",
    default=_Config.max_allowed_files,
    type=int,
    help="maximum number of files allowed in the distribution",
)
@click.option(
    "--max-allowed-size-compressed",
    default=_Config.max_allowed_size_compressed,
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
    default=_Config.max_allowed_size_uncompressed,
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
    filepaths: str,
    inspect: bool,
    max_allowed_files: int,
    max_allowed_size_compressed: str,
    max_allowed_size_uncompressed: str,
) -> None:
    """
    Run the contents of a distribution through a set of checks, and warn about
    any problematic characteristics that are detected.
    """
    print("\n==================== running pydistcheck ====================")
    filepaths_to_check = [click.format_filename(f) for f in filepaths]
    config = _Config()
    kwargs = {
        "inspect": inspect,
        "max_allowed_files": max_allowed_files,
        "max_allowed_size_compressed": max_allowed_size_compressed,
        "max_allowed_size_uncompressed": max_allowed_size_uncompressed,
    }
    kwargs_that_differ_from_defaults = {}
    for k, v in kwargs.items():
        if v != getattr(config, k):
            kwargs_that_differ_from_defaults[k] = v
    config.update_from_toml(toml_file="pyproject.toml")
    config.update_from_dict(input_dict=kwargs_that_differ_from_defaults)

    checks = [
        _DistroTooLargeCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=config.max_allowed_size_compressed
            ).total_size_bytes
        ),
        _DistroTooLargeUnCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=config.max_allowed_size_uncompressed
            ).total_size_bytes
        ),
        _FileCountCheck(max_allowed_files=config.max_allowed_files),
        _FilesOnlyDifferByCaseCheck(),
        _SpacesInPathCheck(),
        _NonAsciiCharacterCheck(),
    ]

    any_errors_found = False
    for filepath in filepaths_to_check:
        print(f"\nchecking '{filepath}'")

        if config.inspect:
            inspect_distribution(filepath=filepath)

        summary = _DistributionSummary.from_file(filename=filepath)
        errors: List[str] = []
        for this_check in checks:
            errors += this_check(distro_summary=summary)

        for i, error_msg in enumerate(errors):
            print(f"{i + 1}. {error_msg}")

        num_errors_for_this_file = len(errors)
        if num_errors_for_this_file:
            any_errors_found = True

        print(f"errors found while checking: {num_errors_for_this_file}")

    print("\n==================== done running pydistcheck ===============")

    # now that all files have been checked, be sure to exit with a non-0 code
    # if any errors were found
    sys.exit(int(any_errors_found))
