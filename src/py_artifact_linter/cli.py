import os
import click
from py_artifact_linter._compat import tomllib
from py_artifact_linter.distribution_summary import summarize_distribution_contents

from typing import Any, Dict, Optional, Union


@click.group()
@click.pass_context
def cli(ctx):
    """Command group just used to group all others as sub-commands of ``py-artifact-linter``"""
    options: Dict[str, Union[int, str]] = {}
    if os.path.exists("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            config_dict = tomllib.load(f)
            options = config_dict.get("tool", {}).get("py-artifact-linter", {})
    ctx.obj = options


@cli.command()
@click.option("--file", "-f", default=None, help="Source distribution (.tar.gz) to check")
@click.pass_obj
def check(tool_options: Dict[str, Any], file: str) -> None:
    """
    Check the contents of a distribution.
    :param file: A file path.
    """
    print("running py-artifact-linter")
    print(file)
    print("pyproject options")
    print(tool_options)


@cli.command()
@click.option("--file", "-f", help="Source distribution (.tar.gz) to check")
@click.option("--output-file", default=None, help="Path to a CSV file to write results to.")
def summarize(file: str, output_file: Optional[str]) -> None:
    """Print a summary of a distribution's contents"""
    summarize_distribution_contents(file=file, output_file=output_file)
