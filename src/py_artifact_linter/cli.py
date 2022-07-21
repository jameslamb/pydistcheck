import click
from py_artifact_linter.distribution_summary import summarize_distribution_contents

from typing import Optional


@click.group()
def cli():
    """Command group just used to group all others as sub-commands of ``py-artifact-linter``"""
    pass


@cli.command()
@click.option(
    "--file", "-f", default=None, help="Source distribution (.tar.gz) to check"
)
def check(file: str) -> None:
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
def summarize(file: str, output_file: Optional[str]) -> None:
    """Print a summary of a distribution's contents"""
    summarize_distribution_contents(file=file, output_file=output_file)
