# Testkraken

Use _Testkraken_ to test workflows in a matrix of parametrized environments.

## Preparing workflow for testing

* each workflow should have a separate dictionary under `workflows4regtests`
* the workflow with command line interface should be in the `workflow` subdirectory
* all input data needed to run the workflow should be under the `data_input` subdirectory
* all reference results should be saved in the `data_ref` subdirectory
* each workflow should have `parameters.yaml` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs.

```yaml
command: python
env:
  base:
  - {image: ubuntu:16.04, pkg-manager: apt}
  - {image: centos:7, pkg-manager: apt}
  fsl:
  - {version: 5.0.9}
  - {version: 5.0.10}
  miniconda:
  - {conda_install: [python=3.5, nipype, pandas, requests]}
inputs:
- [string, --key, 11an55u9t2TAf0EV2pHN0vOd8Ww2Gie-tHp9xGULh_dA]
- [int, -n, '3']
plots:
- function: scatter_all
  var_list: []
- function: scatter_2var
  var_list:
  - [reg:rel_error:white, reg:rel_error:gray]
  - [reg:rel_error:Right-Hippocampus, reg:rel_error:Right-Amygdala]
- function: barplot_all_rel_error
  var_list: []
script: run_demo_workflow.py
tests:
- file: [output/AnnArbor_sub16960/segstats.json, output/AnnArbor_sub20317/segstats.json,
    output/AnnArbor_sub38614/segstats.json]
  name: reg
  script: check_output.py
```
