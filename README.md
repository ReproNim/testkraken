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
            "-f",
            "list2sort.json"
        ]
    ],
    "script": "sorting.py",
    "tests": [
        [
            "list_sorted.json",
            "test_obj_eq"
        ],
        [
            "sum_list.json",
            "test_obj_eq"
        ]
    ]
}
```