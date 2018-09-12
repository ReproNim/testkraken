"""Running workflows and regression tests for all projects in chosen dictionary"""

import os, glob, pdb

from workflowregtest import WorkflowRegtest

Workflows_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "workflows4regtests")

if __name__ == "__main__":
    for workflow in glob.glob(Workflows_dir + "/*/*/"): # assuming that there are 2 levels of directories
        print("workflow all", workflow)
        if "AFNI" in workflow:
            print("Workflow Name ", workflow)
            wf = WorkflowRegtest(os.path.join(Workflows_dir, workflow))
            wf.run()
            wf.merging_all_output()
            wf.dashboard_workflow()
