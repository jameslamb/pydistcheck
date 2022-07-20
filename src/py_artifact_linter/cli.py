import click

@click.group()
def cli():
    """Command group just used to group all others as sub-commands of ``py-artifact-linter``"""
    pass

@cli.command()
@click.option("--file", "-f", default=None, help="Comma-delimited list of doppel output files.")
def check(file: str) -> None:
    """
    Check the contents of a distribution.
    :param file: A file path.
    """
    print("running py-artifact-linter")
    print(file)
