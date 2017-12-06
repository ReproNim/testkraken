"""Methods to generate Dockerfiles with Neurodocker.


Example
-------
```python
import os
import tempfile

from testrunner import WorkflowRegtest
from container_generator import (create_matrix_of_envs,
                                 get_dict_of_neurodocker_dicts,
                                 generate_dockerfile)

wf = WorkflowRegtest('workflows4regtests/basic_examples/sorting_list/')
matrix = create_matrix_of_envs(wf.parameters['env'])
mapping = get_dict_of_neurodocker_dicts(matrix)

tmpdir = tempfile.TemporaryDirectory(prefix="tmp-json-files-",
                                     dir=os.getcwd())
os.mkdir(os.path.join(tmpdir.name, 'json'))
keep_tmpdir = True

try:
    for sha1, neurodocker_dict in mapping.items():
        generate_dockerfile(tmpdir.name, neurodocker_dict, sha1)

except Exception as e:
    raise
finally:
    if not keep_tmpdir:
        tmpdir.cleanup()
```

"""

import itertools
import json
import os


def create_matrix_of_envs(env_params):
    """Create matrix of all combinations of environment variables."""
    params_as_strings = []
    for key, val in env_params.items():
        if isinstance(val, (list, tuple)):
            formatted = tuple("{}::{}".format(key, vv) for vv in val)
        else:
            formatted = tuple("{}::{}".format(key, val))
        params_as_strings.append(formatted)

    matrix_of_envs = list(itertools.product(*params_as_strings))

    for ii, specs in enumerate(matrix_of_envs):
        matrix_of_envs[ii] = [string.split('::') for string in specs]

    return matrix_of_envs


def list_to_neurodocker_instruction(iterable):
    """Return a program entry compatible with Neurodocker.

    Example
    -------
    >>> list_to_neurodocker_instruction(['fsl', '5.0.10'])
    ('fsl', {'version': '5.0.10'})
    """
    program_name, version = iterable

    if program_name in ['python']:
        program_name = "miniconda"
        conda_install = 'python={}'.format(version)
        spec = {
            'conda_install': conda_install,
            'env_name': "test",
        }
    elif program_name in ['base']:
        spec = version
    else:
        spec = {
            'version': version,
        }
    return (program_name, spec)


def instructions_to_neurodocker_specs(instructions):
    """Return dictionary compatible with Neurodocker given a list of
    instructions.
    """
    return {
        "pkg_manager": "apt",
        "check_urls": False,
        "instructions": instructions
    }


def get_dictionary_hash(d):
    """Return SHA-1 hash of dictionary `d`."""
    import hashlib
    import json

    sha1 = hashlib.sha1(json.dumps(d, sort_keys=True).encode())
    return sha1.hexdigest()


def get_dict_of_neurodocker_dicts(env_matrix):
    """Return dictionary of Neurodocker dictionaries given a matrix of
    environment parameters. Keys are the SHA-1 hashes of the Neurodocker
    dictionaries.
    """
    dict_of_neurodocker_dicts = {}
    for ii, params in enumerate(env_matrix):
        instructions = tuple(list_to_neurodocker_instruction(ii)
                             for ii in params)
        neurodocker_dict = instructions_to_neurodocker_specs(instructions)
        this_hash = get_dictionary_hash(neurodocker_dict)
        dict_of_neurodocker_dicts[this_hash] = neurodocker_dict
    return dict_of_neurodocker_dicts


def _generate_dockerfile(dir_, neurodocker_dict, sha1):
    """Return string representation of Dockerfile with the Neurodocker Docker
    image.
    """
    import subprocess

    filepath = os.path.join(dir_, "json", "{}.json".format(sha1))

    with open(filepath, "w") as fp:
        json.dump(neurodocker_dict, fp, indent=4)

    base_cmd = (
        "docker run --rm -v {dir}/json:/json:ro kaczmarj/neurodocker:master"
        " generate --file /json/{filepath}"
    )

    basename = os.path.basename(filepath)
    cmd = base_cmd.format(dir=dir_,
                          filepath=basename)
    output = subprocess.check_output(cmd.split())
    return output.decode()


def generate_dockerfile(dir_, neurodocker_dict, sha1):
    """Generate and save Dockerfiles to `dir_`."""
    dockerfile = _generate_dockerfile(dir_, neurodocker_dict, sha1)
    path = "Dockerfile.{}".format(sha1)
    path = os.path.join(dir_, path)

    with open(path, 'w') as fp:
        fp.write(dockerfile)
