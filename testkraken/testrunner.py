"""Running workflows and regression tests for all projects in chosen dictionary"""

from testkraken.workflowregtest import WorkflowRegtest
import os, pdb


def runner(workflow_path, working_dir=None, tmp_dir=True):
    print("Workflow Name: {}".format(os.path.basename(workflow_path)))
    wf = WorkflowRegtest(
        workflow_path=workflow_path, working_dir=working_dir, tmp_working_dir=tmp_dir
    )
    wf.run()
    wf.merge_outputs()
    wf.dashboard_workflow()
