# TestKraken  

<img style="float: right;" src="testkraken/dashboard_template/images/TestKraken_final.png" width="250">

Use _Testkraken_ to test workflows in a matrix of parametrized environments.

## Installation

_Testkraken_ can be installed with `pip`:

```bash
$ pip install testkraken
```

Developers should use the development installation:

```bash
$ pip install -e .[dev]
```

## Preparing workflow for testing

Here is a directory tree of a valid _Testkraken_ workflow:

```
workflows4regtests/basic_examples/sorting_list_fixedenv
├── data
│    ├── avg_list.json	
│    ├── list2sort.json
│    └── list_sorted.json
│        
├── scripts
│    ├── my_test_obj_eq.py	
│    └── sorting.py
│        
└── parameters.yaml

```

* the `scripts` subdirectory contains the analysis script with command line interface; it can also include user defined tests
* all input data needed to run the workflow and all reference results should be under one directory, the `data` subdirectory is assumed as the default path
* each workflow should have `parameters.yaml` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs.

### `parameters.yaml`

```yaml
# List all desired combinations of environment specifications. This
# configuration, for example, will produce four different Docker images:
#  1. ubuntu 16.04 + python=3.5
#  2. ubuntu 16.04 + python=2.7
#  3. debian:stretch + python=3.5
#  4. debian:stretch + python=2.7
env:
  base:
  - {image: ubuntu:16.04, pkg-manager: apt}
  - {image: debian:stretch, pkg-manager: apt}
  miniconda:
  - {conda_install: [python=3.5]}
  - {conda_install: [python=2.7]}


# One or more fixed environments to test. These environments are built as defined
# and are not combined in any way. This configuration, for example, will
# produce one Docker image.
fixed_env:
  base: {image: debian:stretch, pkg-manager: apt}
  miniconda: {conda_install: [python=3.7]}

# The analysis part: inputs to the analysis script,
# the command to run the script and the script with the analysis.
analysis:
  inputs:
  - {type: File, argstr: -f, value: list2sort.json}
  command: python
  script: sorting.py

# Tests to compare the output of the script to reference data.
# The scripts are available under the user defined `script` subdirectory
# or the `testkraken/testing_functions` directory.
tests:
- {file: list_sorted.json, name: regr1, script: test_obj_eq.py}
- {file: list_sorted.json, name: regr1a, script: my_test_obj_eq.py}
- {file: avg_list.json, name: regr2, script: test_obj_eq.py}
```

## Thanks
Huge thanks to Puck Reeders for creating the logo and Anisha Keshavan for help with the dashboard.
