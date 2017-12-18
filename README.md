# Regression tests

## Preparing workflow for testing 

* each workflow should have a separate dictionary under `workflows4regtests`
* the workflow with command line interface should be in the `workflow` subdirectory
* all input data needed to run the workflow should be under the `data_input` subdirectory
* all reference results should be saved in the `data_ref` subdirectory
* each workflow should have `parameters.json` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs, e.g.

```
{
    "command": "python",
    "env": {
        "base": [
            "debian:stretch",
            "ubuntu:17.04"
        ],
        "python": [
            "2.7",
            "3.5"
        ]
    },
    "inputs": [
        [
            "File",
            "-f",
            "list2sort.json"
        ]
    ],
    "script": "sorting.py",
    "tests": [
        [
            "list_sorted.json",
            "test_obj_eq.py"
        ],
        [
            "sum_list.json",
            "test_obj_eq"
        ]
    ]
}
```

## Output
Currently only the simplest output is available that show if the tests pass or fail. 
The output is store under Circle Ci Artifacts as"
* text information, e.g. [here](https://55-111057450-gh.circle-artifacts.com/0/home/circleci/regtests/report_test_pseudo_random_numbers_debianstretch_3.5.txt)
* simple plot, e.g. [here](https://55-111057450-gh.circle-artifacts.com/0/home/circleci/regtests/fig_pseudo_random_numbers.pdf)