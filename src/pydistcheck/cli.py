import os
import sys
import click
from pydistcheck._compat import tomllib
from pydistcheck.checks import _FileCountCheck
from pydistcheck.distribution_summary import (
    _DistributionSummary,
    summarize_distribution_contents,
)

from typing import Any, Dict, List, Optional, Union


@click.group()
@click.pass_context
def cli(ctx):
    """Command group just used to group all others as sub-commands of ``pydistcheck``"""
    options: Dict[str, Union[int, str]] = {}
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            config_dict = tomllib.load(f)
            options = config_dict.get("tool", {}).get("pydistcheck", {})
    ctx.obj = options


@click.command()
@click.argument(
    "filename",
    type=click.Path(exists=True),
)
@click.option(
    "--max-allowed-files",
    default=2000,
    type=int,
    help="maximum number of files allowed in the distribution",
)
def check(filename: str, max_allowed_files: int) -> None:
    """
    Run the contents of a distribution through a set of checks, and raise
    errors if those are not met.
    :param file: A file path.
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

    checks = [_FileCountCheck(max_allowed_files=max_allowed_files)]

    summary = _DistributionSummary.from_file(filename=click.format_filename(filename))
    errors: List[str] = []
    for this_check in checks:
        errors += this_check(distro_summary=summary)

    for i, error_msg in enumerate(errors):
        print(f"{i + 1}. {error_msg}")

    print(f"errors found while checking: {len(errors)}")
    sys.exit(len(errors))

    # surprising / disallowed file extensions
    # included test files
    # found executable files
    # wheel contains compiled objects/libraries with debug symbols
    # total compressed size > {some_threshold}
    # total uncompressed size > {some_threshold}
    # found files with spaces in their names
    # found file paths longer than {} characters
    # found files with names containing control characters
    # more than {n} total files
    # found files with compressed size > {some_threshold}


@click.command()
@click.argument(
    "filename",
    type=click.Path(exists=True),
)
@click.option("--output-file", default=None, help="Path to a CSV file to write results to.")
def summarize(filename: str, output_file: Optional[str]) -> None:
    """Print a summary of a distribution's contents"""
    summarize_distribution_contents(file=click.format_filename(filename), output_file=output_file)
