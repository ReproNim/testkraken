import os, pdb
import pytest

from testkraken.workflowregtest import WorkflowRegtest

Workflows_main_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                "../../workflows4regtests", "basic_examples",)
workflows_list = [os.path.join(Workflows_main_dir, workf) for workf in next(os.walk(Workflows_main_dir))[1]]

@pytest.mark.parametrize("workflow_dir", workflows_list)
def test_basic_examples(workflow_dir):
    print(workflow_dir)
    try:
        wf = WorkflowRegtest(workflow_dir)
        wf.run()
        wf.merge_outputs()
        wf.dashboard_workflow()
    except Exception as e:
        print(e)
        assert False
