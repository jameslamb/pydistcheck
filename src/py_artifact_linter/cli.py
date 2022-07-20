import click
from py_artifact_linter.distribution_summary import summarize_distribution_contents


@click.group()
def cli():
    """Command group just used to group all others as sub-commands of ``py-artifact-linter``"""
    pass


@cli.command()
@click.option(
    "--file", "-f", default=None, help="Comma-delimited list of doppel output files."
)
def check(file: str) -> None:
    """
    Check the contents of a distribution.
    :param file: A file path.
    """
    print("running py-artifact-linter")
    print(file)


@cli.command()
@click.option(
    "--file", "-f", default=None, help="Comma-delimited list of doppel output files."
)
def summarize(file: str) -> None:
    """Print a summary of a distribution's contents"""
    summarize_distribution_contents(file=file)
