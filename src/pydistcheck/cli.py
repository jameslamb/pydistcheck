"""
CLI entrypoints
"""

import sys
from typing import List

import click

from pydistcheck.checks import (
    ALL_CHECKS,
    _CompiledObjectsDebugSymbolCheck,
    _DistroTooLargeCompressedCheck,
    _DistroTooLargeUnCompressedCheck,
    _FileCountCheck,
    _FilesOnlyDifferByCaseCheck,
    _NonAsciiCharacterCheck,
    _SpacesInPathCheck,
    _UnexpectedFilesCheck,
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
    "--ignore",
    type=str,
    default=_Config.ignore,
    help=(
        "comma-separated list of checks to skip, e.g. "
        "``distro-too-large-compressed,path-contains-spaces``."
    ),
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
    show_default=True,
    type=int,
    help="maximum number of files allowed in the distribution",
)
@click.option(
    "--max-allowed-size-compressed",
    default=_Config.max_allowed_size_compressed,
    show_default=True,
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
    show_default=True,
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
@click.option(
    "--unexpected-directory-patterns",
    default=_Config.unexpected_directory_patterns,
    show_default=True,
    type=str,
    help=(
        "comma-delimited list of patterns matching directories that are not expected "
        "to be found in the distribution. Patterns should be in the format understood "
        "by ``fnmatch.fnmatchcase()``. See https://docs.python.org/3/library/fnmatch.html."
    ),
)
@click.option(
    "--unexpected-file-patterns",
    default=_Config.unexpected_file_patterns,
    show_default=True,
    type=str,
    help=(
        "comma-delimited list of patterns matching files that are not expected "
        "to be found in the distribution. Patterns should be in the format understood "
        "by ``fnmatch.fnmatchcase()``. See https://docs.python.org/3/library/fnmatch.html."
    ),
)
def check(  # pylint: disable=too-many-arguments
    filepaths: str,
    ignore: str,
    inspect: bool,
    max_allowed_files: int,
    max_allowed_size_compressed: str,
    max_allowed_size_uncompressed: str,
    unexpected_directory_patterns: str,
    unexpected_file_patterns: str,
) -> None:
    """
    Run the contents of a distribution through a set of checks, and warn about
    any problematic characteristics that are detected.
    """
    print("==================== running pydistcheck ====================")
    filepaths_to_check = [click.format_filename(f) for f in filepaths]
    config = _Config()
    kwargs = {
        "ignore": ignore,
        "inspect": inspect,
        "max_allowed_files": max_allowed_files,
        "max_allowed_size_compressed": max_allowed_size_compressed,
        "max_allowed_size_uncompressed": max_allowed_size_uncompressed,
        "unexpected_directory_patterns": unexpected_directory_patterns,
        "unexpected_file_patterns": unexpected_file_patterns,
    }
    kwargs_that_differ_from_defaults = {}
    for k, v in kwargs.items():
        if v != getattr(config, k):
            kwargs_that_differ_from_defaults[k] = v
    config.update_from_toml(toml_file="pyproject.toml")
    config.update_from_dict(input_dict=kwargs_that_differ_from_defaults)

    checks_to_ignore = {x for x in config.ignore.split(",") if x.strip() != ""}
    unrecognized_checks = checks_to_ignore - ALL_CHECKS
    if unrecognized_checks:
        # converting to list + sorting here so outputs are deterministic
        # (since sets don't guarantee ordering)
        error_str = ",".join(sorted(unrecognized_checks))
        print(f"ERROR: found the following unrecognized checks passed via '--ignore': {error_str}")
        sys.exit(1)

    checks = [
        _CompiledObjectsDebugSymbolCheck(),
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
        _UnexpectedFilesCheck(
            unexpected_directory_patterns=unexpected_directory_patterns.split(","),
            unexpected_file_patterns=unexpected_file_patterns.split(","),
        ),
        _NonAsciiCharacterCheck(),
    ]

    # filter out ignored checks
    checks = [c for c in checks if c.check_name not in checks_to_ignore]

    any_errors_found = False
    for filepath in filepaths_to_check:
        print(f"\nchecking '{filepath}'")

        if config.inspect:
            print("----- package inspection summary -----")
            inspect_distribution(filepath=filepath)

        print("------------ check results -----------")
        summary = _DistributionSummary.from_file(filename=filepath)
        errors: List[str] = []
        for this_check in checks:
            errors += this_check(distro_summary=summary)

        for i, error_msg in enumerate(sorted(errors)):
            print(f"{i + 1}. {error_msg}")

        num_errors_for_this_file = len(errors)
        if num_errors_for_this_file:
            any_errors_found = True

        print(f"errors found while checking: {num_errors_for_this_file}")

    print("\n==================== done running pydistcheck ===============")

    # now that all files have been checked, be sure to exit with a non-0 code
    # if any errors were found
    sys.exit(int(any_errors_found))
