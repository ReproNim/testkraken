"""Running workflows and regression tests for all projects in chosen dictionary"""

import os

from workflowregtest import WorkflowRegtest

Workflows_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                             "workflows4regtests", "basic_examples",)

if __name__ == "__main__":
    for workflow in next(os.walk(Workflows_dir))[1]:
        if "simple" in workflow:
            print("Workflow Name ", workflow)
            wf = WorkflowRegtest(os.path.join(Workflows_dir, workflow))
            wf.run()
            wf.merging_all_output()
            # # TODO: this method will be removed
            # wf.plot_all_results_paralcoord()
            wf.dashboard_workflow()
