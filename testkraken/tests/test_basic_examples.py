import os, pdb
import pytest

from testkraken.testrunner import runner

Workflows_main_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "../../workflows4regtests", "basic_examples",)
workflows_list = [os.path.join(Workflows_main_dir, workf) for workf in next(os.walk(Workflows_main_dir))[1]
                  if "sorting_l" in workf]

@pytest.mark.parametrize("workflow_dir", workflows_list)
def test_basic_examples(workflow_dir):
    print(workflow_dir)
    # TODO: should I use try?
    # try:
    runner(workflow_dir)
    # except Exception as e:
    #     print(e)
    #     assert False
