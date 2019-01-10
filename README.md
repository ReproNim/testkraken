# TestKraken

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

Here is a directory tree of a valid _Testkraken_ workflow:

```
workflows4regtests/basic_examples/simple_workflow
├── data_ref
│   └── output
│       ├── AnnArbor_sub16960
│       │   └── segstats.json
│       ├── AnnArbor_sub20317
│       │   └── segstats.json
│       └── AnnArbor_sub38614
│           └── segstats.json
├── parameters.yaml
└── workflow
    └── run_demo_workflow.py
```

* the workflow with command line interface should be in the `workflow` subdirectory
* all input data needed to run the workflow should be under the `data_input` subdirectory
* all reference results should be saved in the `data_ref` subdirectory
* each workflow should have `parameters.yaml` to describe environment, input data, script and command to run the workflow, and chosen tests for the workflow outputs.

### `parameters.yaml`

```yaml
# List all desired combinations of environment specifications. This
# configuration, for example, will produce four different Docker images:
#  1. ubuntu 16.04 + fsl 5.0.9 + miniconda
#  2. ubuntu 16.04 + fsl 5.0.10 + miniconda
#  3. centos 7 + fsl 5.0.9 + miniconda
#  4. centos 7 + fsl5.0.10 + miniconda
env:
  base:
    - image: 'ubuntu:16.04'
      pkg-manager: apt
    - image: 'centos:7'
      pkg-manager: yum
  fsl:
    - version: 5.0.9
    - version: 5.0.10
  miniconda:
    - conda_install:
        - python=3.5
        - nipype
        - pandas
        - requests

# One or more fixed environments to test. These environments are built as defined
# and are not combined in any way. This configuration, for example, will
# produce one Docker image.
fixed_env:
  base:
    image: 'centos:7'
    pkg-manager: yum
  fsl:
    version: 5.0.10
  miniconda:
    conda_install:
      - python=2.7
      - nipype
      - pandas
      - requests
      - bz2file

# The command to run the script.
command: python
# The workflow script. The script must be useable on the command-line.
script: run_demo_workflow.py

# Inputs to the workflow script. The first item is always the CWLType of the
# argument. See https://www.commonwl.org/v1.0/CommandLineTool.html#CWLType for
# all available types.
inputs:
  - [string, --key, 11an55u9t2TAf0EV2pHN0vOd8Ww2Gie-tHp9xGULh_dA]
  - [int, -n, '3']

# Tests to compare the output of the script to reference data.
tests:
  - file:
      - output/AnnArbor_sub16960/segstats.json
      - output/AnnArbor_sub20317/segstats.json
      - output/AnnArbor_sub38614/segstats.json
    # A descriptive name for the test.
    name: regr
    # These scripts are available under `testkraken/testing_functions`.
    script: check_output.py
```
