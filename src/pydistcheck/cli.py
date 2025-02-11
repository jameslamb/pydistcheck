"""
CLI entrypoints
"""

import sys
from typing import List, Sequence

import click

from pydistcheck import __version__ as _VERSION

from ._checks import (
    ALL_CHECKS,
    _CompiledObjectsDebugSymbolCheck,
    _DistroTooLargeCompressedCheck,
    _DistroTooLargeUnCompressedCheck,
    _ExpectedFilesCheck,
    _FileCountCheck,
    _FilesOnlyDifferByCaseCheck,
    _MixedFileExtensionCheck,
    _NonAsciiCharacterCheck,
    _PathTooLongCheck,
    _SpacesInPathCheck,
    _UnexpectedFilesCheck,
)
from ._config import _Config
from ._distribution_summary import _DistributionSummary
from ._inspect import inspect_distribution
from ._utils import _FileSize


class ExitCodes:
    OK = 0
    CHECK_ERRORS = 1
    UNSUPPORTED_FILE_TYPE = 2


@click.command()
@click.argument(
    "filepaths",
    type=click.Path(exists=True),
    nargs=-1,
)
@click.option(
    "--version",
    is_flag=True,
    show_default=False,
    default=False,
    help="Print the version of pydistcheck and exit.",
)
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help=(
        "Path to a TOML file containing a [tool.pydistcheck] table. "
        "If provided, pyproject.toml will be ignored."
    ),
)
@click.option(
    "--ignore",
    multiple=True,
    default=_Config.ignore,
    help=(
        "ID of a check to skip, e.g. 'compiled-objects-have-debug-symbols'. "
        "See https://pydistcheck.readthedocs.io/en/docs-fix/check-reference.html for a "
        "complete list of valid options. Can be passed multiple times."
    ),
)
@click.option(
    "--select",
    multiple=True,
    default=_Config.select,
    help=(
        "ID of a check to include, e.g. 'compiled-objects-have-debug-symbols'. "
        "If this is provided even once, pydistcheck will only run the checks specified this way. "
        "See https://pydistcheck.readthedocs.io/en/docs-fix/check-reference.html for a "
        "complete list of valid options. Can be passed multiple times."
    ),
)
@click.option(
    "--inspect",
    is_flag=True,
    show_default=False,
    default=_Config.inspect,
    help=(
        "Print a summary of the distribution, like its total size and largest files."
    ),
)
@click.option(
    "--expected-directories",
    multiple=True,
    default=_Config.expected_directories,
    show_default=True,
    help=(
        "Pattern matching directories that are expected to be found in the distribution. "
        "Prefix with '!' to indicate a pattern which should NOT match any of the distribution's "
        "contents. Other than that possible leading '!', patterns should be in the format understood by "
        "``fnmatch.fnmatchcase()`` (https://docs.python.org/3/library/fnmatch.html). "
        "Can be passed multiple times."
    ),
)
@click.option(
    "--expected-files",
    multiple=True,
    default=_Config.expected_files,
    show_default=True,
    help=(
        "Pattern matching files that are expected to be found in the distribution. "
        "Prefix with '!' to indicate a pattern which should NOT match any of the distribution's "
        "contents. Other than that possible leading '!', patterns should be in the format understood by "
        "``fnmatch.fnmatchcase()`` (https://docs.python.org/3/library/fnmatch.html). "
        "Can be passed multiple times."
    ),
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
        "maximum allowed compressed size, a string like '1.5MB' indicating"
        " '1.5 megabytes'. Supported units:\n"
        "  - B = bytes\n"
        "  - KB = kilobytes\n"
        "  - K, Ki = kibibytes\n"
        "  - MB = megabytes\n"
        "  - M, Mi = mebibytes\n"
        "  - GB = gigabytes\n"
        "  - G, Gi = gibibytes"
    ),
)
@click.option(
    "--max-allowed-size-uncompressed",
    default=_Config.max_allowed_size_uncompressed,
    show_default=True,
    type=str,
    help=(
        "maximum allowed uncompressed size, a string like '1.5MB' indicating"
        " '1.5 megabytes'. Supported units:\n"
        "  - B = bytes\n"
        "  - KB = kilobytes\n"
        "  - K, Ki = kibibytes\n"
        "  - MB = megabytes\n"
        "  - M, Mi = mebibytes\n"
        "  - GB = gigabytes\n"
        "  - G, Gi = gibibytes"
    ),
)
@click.option(
    "--max-path-length",
    default=_Config.max_path_length,
    show_default=True,
    type=int,
    help="Maximum allowed filepath length for files or directories in the distribution.",
)
@click.option(
    "--output-file-size-precision",
    default=_Config.output_file_size_precision,
    show_default=True,
    type=int,
    help=(
        "Number of significant digits to use when rounding file sizes in printed output."
    ),
)
@click.option(
    "--output-file-size-unit",
    default=_Config.output_file_size_unit,
    show_default=True,
    type=str,
    help=(
        "Unit for all file sizes reported in outputs (e.g. log messages, --inspect output)"
        " Supported units:\n"
        "  - B = bytes\n"
        "  - KB = kilobytes\n"
        "  - K, Ki = kibibytes\n"
        "  - MB = megabytes\n"
        "  - M, Mi = mebibytes\n"
        "  - GB = gigabytes\n"
        "  - G, Gi = gibibytes"
    ),
)
def check(  # noqa: PLR0913
    *,
    filepaths: str,
    version: bool,
    config: str,
    expected_directories: Sequence[str],
    expected_files: Sequence[str],
    ignore: Sequence[str],
    inspect: bool,
    max_allowed_files: int,
    max_allowed_size_compressed: str,
    max_allowed_size_uncompressed: str,
    max_path_length: int,
    output_file_size_precision: int,
    output_file_size_unit: str,
    select: Sequence[str],
) -> None:
    """
    Run the contents of a distribution through a set of checks, and warn about
    any problematic characteristics that are detected.

    Exit codes:

      0 = no issues detected\n
      1 = issues detected
    """
    if version:
        print(f"pydistcheck {_VERSION}")
        sys.exit(ExitCodes.OK)

    print("==================== running pydistcheck ====================")
    filepaths_to_check = [click.format_filename(f) for f in filepaths]
    conf = _Config()
    kwargs = {
        "ignore": ignore,
        "inspect": inspect,
        "max_allowed_files": max_allowed_files,
        "max_allowed_size_compressed": max_allowed_size_compressed,
        "max_allowed_size_uncompressed": max_allowed_size_uncompressed,
        "max_path_length": max_path_length,
        "output_file_size_precision": output_file_size_precision,
        "output_file_size_unit": output_file_size_unit,
        "select": select,
        "expected_directories": expected_directories,
        "expected_files": expected_files,
    }
    kwargs_that_differ_from_defaults = {
        k: v for k, v in kwargs.items() if v != getattr(conf, k)
    }
    if config is not None:
        conf.update_from_toml(toml_file=click.format_filename(config))
    else:
        conf.update_from_toml(toml_file="pyproject.toml")
    conf.update_from_dict(input_dict=kwargs_that_differ_from_defaults)

    checks_to_ignore = {x for x in conf.ignore if x.strip()}
    unrecognized_checks = checks_to_ignore - ALL_CHECKS
    if unrecognized_checks:
        # converting to list + sorting here so outputs are deterministic
        # (since sets don't guarantee ordering)
        error_str = ",".join(sorted(unrecognized_checks))
        print(
            f"ERROR: found the following unrecognized checks passed via '--ignore': {error_str}"
        )
        sys.exit(1)

    selected_checks = {x for x in conf.select if x.strip()}
    unrecognized_checks = selected_checks - ALL_CHECKS
    if unrecognized_checks:
        # converting to list + sorting here so outputs are deterministic
        # (since sets don't guarantee ordering)
        error_str = ",".join(sorted(unrecognized_checks))
        print(
            f"ERROR: found the following unrecognized checks passed via '--select': {error_str}"
        )
        sys.exit(1)

    checks = [
        _CompiledObjectsDebugSymbolCheck(),
        _DistroTooLargeCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=conf.max_allowed_size_compressed
            ).total_size_bytes,
            output_file_size_precision=conf.output_file_size_precision,
            output_file_size_unit=conf.output_file_size_unit,
        ),
        _DistroTooLargeUnCompressedCheck(
            max_allowed_size_bytes=_FileSize.from_string(
                size_str=conf.max_allowed_size_uncompressed
            ).total_size_bytes,
            output_file_size_precision=conf.output_file_size_precision,
            output_file_size_unit=conf.output_file_size_unit,
        ),
        _ExpectedFilesCheck(
            directory_patterns=expected_directories,
            file_patterns=expected_files,
        ),
        _FileCountCheck(max_allowed_files=conf.max_allowed_files),
        _FilesOnlyDifferByCaseCheck(),
        _MixedFileExtensionCheck(),
        _PathTooLongCheck(max_path_length=conf.max_path_length),
        _SpacesInPathCheck(),
        _UnexpectedFilesCheck(
            directory_patterns=expected_directories,
            file_patterns=expected_files,
        ),
        _NonAsciiCharacterCheck(),
    ]

    # if 'select' is non-empty, use only the checks indicated by that option
    if selected_checks:
        checks = [c for c in checks if c.check_name in selected_checks]
    # otherwise, run all checks except those indicated by 'ignore'
    elif checks_to_ignore:
        checks = [c for c in checks if c.check_name not in checks_to_ignore]

    any_errors_found = False
    for filepath in filepaths_to_check:
        print(f"\nchecking '{filepath}'")

        try:
            summary = _DistributionSummary.from_file(filename=filepath)
        except ValueError as err:
            print(f"error: {err}")
            sys.exit(ExitCodes.UNSUPPORTED_FILE_TYPE)

        if conf.inspect:
            print("----- package inspection summary -----")
            inspect_distribution(
                summary=summary,
                config=conf,
            )

        print("------------ check results -----------")
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
    if any_errors_found:
        sys.exit(ExitCodes.CHECK_ERRORS)
    else:
        sys.exit(ExitCodes.OK)
