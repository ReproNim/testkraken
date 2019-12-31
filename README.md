# TestKraken  

<img style="float: right;" src="testkraken/dashboard_template/images/TestKraken_final.png" width="250">

Use _TestKraken_ to test workflows in a matrix of parametrized environments.

## Installation

_TestKraken_ can be installed with `pip`:

```bash
$ pip install testkraken
```

Developers should use the development installation:

```bash
$ pip install -e .[dev]
```

## Preparing the workflow for testing

Here is a directory tree of a valid _TestKraken_ workflow:

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
└── testkraken_spec.yml

```

* The `scripts` subdirectory is the deafult place for the directory that contains the analysis script with command line interface; it can also include user defined tests.
* The `data` subdirectory is the deafult place for the directory that contains all input data needed to run the workflow and all reference results.
* Each workflow should have `testkraken_spec.yml` to describe environments, input data, script and command to run the workflow, and chosen tests for the workflow outputs.

## TestKraken Specification

Specification should be included in `testkraken_spec.yml` file, that should be in the main workflow directory (see above).

### Specification of the computational environments
The computational environments for the tested analysis can be described in `env` or `fixed_env` (one or both elements have to be specified in the specification). The _Dockerfiles_ to generate the images will be created using [Neurodocker](https://github.com/ReproNim/neurodocker), so the components of both entries, `env` and `fixed_env`, are specified in the _Neurodocker_ specification. There is one difference, that `base` part should contain `image` and `pkg-manager` in one dictionary.

#### `env` and `fixed_env` elements
Both `env` and `fixed_env` are used to specify multiple environments. In the `env` part, each _Neurodocker_ key (e.g. `base`, `miniconda`, `fsl`) can be a list, and _TestKraken_ will create all desired combinations of environment specifications. The `fixed_env` can provide an additional specification for an environment or a list of complete specifications. The _Neurodocker_ keys must be the same for `env` and all elements of the `fixed_env` part.

This is an example of the environment specification that makes use of `env` and `fixed_env` elements:

```yaml
# List all desired combinations of environment specifications. This
# configuration, for example, will produce four different Docker images:
#  1. ubuntu 16.04 + python=3.5, numpy
#  2. ubuntu 16.04 + python=2.7, numpy
#  3. debian:stretch + python=3.5, numpy
#  4. debian:stretch + python=2.7, numpy
env:
  base:
  - {image: ubuntu:16.04, pkg-manager: apt}
  - {image: debian:stretch, pkg-manager: apt}
  miniconda:
  - {conda_install: [python=3.5, numpy]}
  - {conda_install: [python=2.7, numpy]}


# One or more fixed environments to test. These environments are built as defined
# and are not combined in any way. This configuration, for example, will
# produce one Docker image.
fixed_env:
  base: {image: debian:stretch, pkg-manager: apt}
  miniconda: {conda_install: [python=3.7, numpy]}
```
Example that uses the concept can be found [here](https://github.com/ReproNim/testkraken/blob/master/workflows4regtests/basic_examples/sorting_list_fixedenv/testkraken_spec.yml)

#### `common` and `varied` parts
In order to eliminate repetition in the `env` part, for each _Neurodocker_ key the additional structure can be added to describe `common` and `varied` parts. The previous example could also look like this:
```yaml
env:
  base:
  - {image: ubuntu:16.04, pkg-manager: apt}
  - {image: debian:stretch, pkg-manager: apt}
  miniconda:
    common: {pip_install: [numpy]}
    varied:
    - {conda_install: [python=3.5]}
    - {conda_install: [python=2.7]}
```
Example that uses the concept can be found [here](https://github.com/ReproNim/testkraken/blob/master/workflows4regtests/basic_examples/sorting_array_pip_comvarenv/testkraken_spec.yml)

### Data and Scripts locations

There is a default location where `TestKraken` tries to find all the data files and all the scripts files - this is the root directory of the tested workflow. However, these default locations can be changed via the `testkraken_spec.yml`.

#### `data` element
In order to specify how to get the data, the `data` entry has to have two keys - `type` and `location`. For now, only one `type` is implemented - `workflow_path`, but in the future this might be used to specify external repositories. For `type=workflow_path`, the location is simply the relative directory path to the workflow path. An example can look like this:

```yaml
data:
  type: workflow_path
  location: my_data
```

#### `scripts` element
The `scripts` entry requires only the relative directory path to the workflow path. An example can look like this:

```yaml
scripts: my_scripts
```
Example that uses the concept can be found [here](https://github.com/ReproNim/testkraken/blob/master/workflows4regtests/basic_examples/pseudo_random_numbers/testkraken_spec.yml)

### Analysis part
The `analysis` element contains all the information required to run the workflow with the analysis. There is one required element - `command`, and two optional elements - `script` and `inputs`. These are assembled as `command script input1 input2 ...`. When the `command` is a shell or interpreter (e.g., "bash", "python"), then the `script` is needed. However, the command can be an executable (e.g., "ssh", "bc") and then the `script` option is not required. The `inputs` part contains all the inputs needed to complete the command required to run the analysis. Each element of the `inputs` entry should have `type`, `argstr` (if a flag is needed) and `value`, and might have additional metadata that can be used by [pydra](https://github.com/nipype/pydra) (a dataflow engine used by _TestKraken_). If `type` is `File`, the file is assumed to be relative to the the data directory location. If `script` is provided, the script file is expected to be in the scripts directory. An example can look like this:

```yaml
# The analysis part: inputs to the analysis script,
# the command to run the script and the script with the analysis.
analysis:
  inputs:
  - {type: File, argstr: -f, value: list2sort.json}
  command: python
  script: sorting.py
```

### Tests part
The `tests` part contains all information regarding testing the analysis output. It is assumed that the output file is compared to the reference file that is available in the data directory (with the same name). If the `tests` part is not present or it's empty, no tests will be run after the analysis. There could be multiple entries for `tests`, but each element has to contain `file` with the name of the output file, `name` with the user defined name of the test, and `script` with the name of the script that should be used for running the test. The script can be saved in the script directory (checked first) or it can be an existing test from the `TestKraken` [testing_functions directory](https://github.com/ReproNim/testkraken/tree/master/testkraken/testing_functions). Any user provided tests have to follow the same template as the tests from `TestKraken` and define a command line interface.
Example:

```yaml
# Tests to compare the output of the script to reference data.
# The scripts are available under the user defined `script` subdirectory
# or the `testkraken/testing_functions` directory.
tests:
- {file: list_sorted.json, name: regr1, script: test_obj_eq.py}
- {file: list_sorted.json, name: regr1a, script: my_test_obj_eq.py}
- {file: avg_list.json, name: regr2, script: test_obj_eq.py}
```
Example that uses the concept can be found [here](https://github.com/ReproNim/testkraken/blob/master/workflows4regtests/basic_examples/sorting_list_fixedenv/testkraken_spec.yml)


## Thanks
Huge thanks to Puck Reeders for creating the logo and Anisha Keshavan for help with the dashboard.
