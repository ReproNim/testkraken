# Regression tests

## Preparing workflow for testing

* each workflow should have a separate dictionary under `workflows4regtests`
* the workflow with command line interface should be in the `workflow` subdirectory
* all input data needed to run the workflow should be under the `data_input` subdirectory
* all reference results should be saved in the `data_ref` subdirectory
* each workflow should have `parameters.json` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs, e.g.

```json
{
    "command": "python",
    "env": {
        "base": [
            "debian:stretch",
            "ubuntu:17.04"
        ],
        "conda_env_yml": [
            "environment_py2.yml",
            "environment_py3.yml"
        ],
        "fsl": [
            "5.0.9",
            "5.0.10"
        ]
    },
    "inputs": [
        [
            "string",
            "--key",
            "11an55u9t2TAf0EV2pHN0vOd8Ww2Gie-tHp9xGULh_dA"
        ],
        [
            "int",
            "-n",
            "1"
        ]
    ],
    "script": "run_demo_workflow.py",
    "tests": [
        [
             "output/metaflow/AnnArbor_sub16960/save_json/segstats.json",
             "check_output.py"
        ]
    ]
}
```

## Output
Currently only the simplest output is available that show if the tests pass or fail.
The output is store under Circle Ci Artifacts as"
* text information, e.g. [here](https://63-111057450-gh.circle-artifacts.com/0/home/circleci/regtests/report_test_simple_workflow_debianstretch_environment_py2.yml_5.0.9.txt)
* simple plot, e.g. [here](https://63-111057450-gh.circle-artifacts.com/0/home/circleci/regtests/fig_simple_workflow.pdf)
