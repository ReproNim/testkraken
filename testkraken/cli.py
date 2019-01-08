"""Command-line interface for Testkraken."""

import click

from testkraken.workflowregtest import WorkflowRegtest


@click.command()
@click.argument('path', type=click.Path(exists=True))
@click.option('-w', '--working-dir', type=click.Path(), help="Working directory of workflow. Default is a temporary directory.")
def main(path, working_dir=None):
    """This script runs the workflow in PATH."""
    wf = WorkflowRegtest(path, working_dir=working_dir)
    wf.run()
    wf.merge_outputs()
    wf.dashboard_workflow()
