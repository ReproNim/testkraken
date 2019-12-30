"""Command-line interface for Testkraken."""

import click

from testkraken.workflowregtest import WorkflowRegtest


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option(
    "-w",
    "--working-dir",
    type=click.Path(),
    help="Working directory of workflow. Default is a temporary directory.",
)
def main(path, working_dir=None, tmp_working_dir=True):
    """This script runs the workflow in PATH."""
    if working_dir:
        tmp_working_dir = False
    wf = WorkflowRegtest(
        workflow_path=path, working_dir=working_dir, tmp_working_dir=tmp_working_dir
    )
    print(f"\n running testkraken for {path}; working directory - {working_dir}")
    wf.run()
    wf.merge_outputs()
    wf.dashboard_workflow()
