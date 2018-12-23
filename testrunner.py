"""Running workflows and regression tests for all projects in chosen dictionary"""

from .workflowregtest import WorkflowRegtest
import os, pdb


#TODO click!
def runner(workflow_dir):
    print("Workflow Name: {}".format(os.path.basename(workflow_dir)))
    wf = WorkflowRegtest(workflow_dir)
    wf.run()
    wf.merging_all_output()
    wf.dashboard_workflow()