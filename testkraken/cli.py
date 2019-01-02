"""Command-line interface for Testkraken."""

import click

@click.command(help="Run the workflow in PATH.")
@click.argument('path', type=click.Path(exists=True))
def main(path):
    print("Not implemented yet. In the future, will run from {}".format(path))
