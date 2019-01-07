# Testkraken

Use _Testkraken_ to test workflows in a matrix of parametrized environments.

## Installation

_Testkraken_ can be installed with `pip`:

```bash
$ pip install .
```

Developers should use the development installation:

```bash
$ pip install -e .[dev]
```

## Preparing workflow for testing

* each workflow should have a separate dictionary under `workflows4regtests`
* the workflow with command line interface should be in the `workflow` subdirectory
* all input data needed to run the workflow should be under the `data_input` subdirectory
* all reference results should be saved in the `data_ref` subdirectory
* each workflow should have `parameters.yaml` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs.

```yaml
# command to run the workflow that is being tested
command: python

# software specification for docker containers (all possible combination)
env:
  base:
  - {image: ubuntu:16.04, pkg-manager: apt}
  - {image: centos:7, pkg-manager: apt}
  fsl:
  - {version: 5.0.9}
  - {version: 5.0.10}
  miniconda:
  - {conda_install: [python=3.5, nipype, pandas, requests]}
  
# softtware specification for a specific docker container
fixed_env:
  base: {image: centos:7, pkg-manager: apt}
  fsl: {version: 5.0.10}
  miniconda: {conda_install: [python=2.7, nipype, pandas, requests, bz2file]}
  
# arguments required to run the workflow
inputs:
- [string, --key, 11an55u9t2TAf0EV2pHN0vOd8Ww2Gie-tHp9xGULh_dA]
- [int, -n, '3']

# name of the file with the workflow script
script: run_demo_workflow.py

# tests specifications including name of the tests and files from the workflow output
tests:
- file: [output/AnnArbor_sub16960/segstats.json, output/AnnArbor_sub20317/segstats.json,
    output/AnnArbor_sub38614/segstats.json]
  name: regr
  script: check_output.py
```
