import os
import click
from dataclasses import dataclass
from py_artifact_linter._compat import tomllib
from py_artifact_linter.distribution_summary import summarize_distribution_contents

from typing import Dict, Optional, Union


@dataclass
class _ConfigOptions:
    summarize: _SummarizeOptions

    @classmethod
    def from_pyproject_file(cls, filepath: str):
        with open(filepath, "rb") as f:
            config_dict = tomllib.load(f)["tool"]["py-artifact-linter"]
        return cls(
            summarize=c
        )


@click.group()
@click.pass_context()
def cli(ctx):
    """Command group just used to group all others as sub-commands of ``py-artifact-linter``"""
    options: Dict[str, Union[int, str]] = {}
    if os.exists("pyproject.toml"):
        with open("pyproject.toml", "rb") as f:
            config_dict = tomllib.load(f)
            options = config_dict.get("tool", {}).get("py-artifact-linter", {})
    ctx.tool_options = options



@cli.command()
@click.option(
    "--file", "-f", default=None, help="Source distribution (.tar.gz) to check"
)
@click.pass_tool_options
def check(tool_options: Dict, file: str) -> None:
    """
    Check the contents of a distribution.
    :param file: A file path.
    """
    print("running py-artifact-linter")
    print(file)


@cli.command()
@click.option("--file", "-f", help="Source distribution (.tar.gz) to check")
@click.option(
    "--output-file", default=None, help="Path to a CSV file to write results to."
)
@click.pass_tool_options
def summarize(tool_options: Dict, file: str, output_file: Optional[str]) -> None:
    """Print a summary of a distribution's contents"""
    summarize_distribution_contents(file=file, output_file=output_file)
