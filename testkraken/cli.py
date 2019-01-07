"""Command-line interface for Testkraken."""

import click

from testkraken.workflowregtest import WorkflowRegtest


@click.command(help="Run the workflow in PATH.")
@click.argument('path', type=click.Path(exists=True))
@click.option('-w', '--working-dir', type=click.Path(), help="Working directory of workflow. Default is a temporary directory.")
def main(path, working_dir=None):
    wf = WorkflowRegtest(path, working_dir=working_dir)
    wf.run()
    wf.merging_all_output()
    wf.dashboard_workflow()
