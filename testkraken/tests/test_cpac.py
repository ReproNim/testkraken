import os
from pathlib import Path
import pytest

from testkraken.testrunner import runner

Workflows_main_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "../../workflows4regtests",
    "cpac",
)
workflows_list = [
    os.path.join(Workflows_main_dir, workf)
    for workf in next(os.walk(Workflows_main_dir))[1]
    if "afni" not in workf
]


@pytest.mark.parametrize("workflow_path", workflows_list)
def test_basic_examples(workflow_path):
    print(workflow_path)
    cwd = Path.cwd()
    working_dir = (cwd / "outputs" / Path(workflow_path).name).absolute()
    # breakpoint()
    runner(workflow_path=workflow_path, working_dir=working_dir)
    os.chdir(cwd)
