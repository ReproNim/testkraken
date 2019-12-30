import os
from pathlib import Path
import pytest

from ..testrunner import runner

Workflows_main_dir = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "../../workflows4regtests", "nfm"
)
workflows_list = [
    os.path.join(Workflows_main_dir, workf)
    for workf in next(os.walk(Workflows_main_dir))[1]
    if "coco" in workf
]


@pytest.mark.parametrize("workflow_path", workflows_list)
def test_afni_examples(workflow_path):
    print(workflow_path)
    cwd = Path.cwd()
    working_dir = (cwd / "outputs" / Path(workflow_path).name).absolute()
    runner(workflow_path=workflow_path, working_dir=working_dir)
    os.chdir(cwd)
