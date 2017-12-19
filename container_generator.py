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
import subprocess
from collections import OrderedDict
import pdb


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
            'activate': "true"
        }
    elif program_name in ['conda_env_yml']:
        program_name = "miniconda"
        env_yml_path = version
        spec = {
            'yaml_file': env_yml_path,
            'env_name': "test",
            'activate': "true"
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
    environment parameters. Keys are the SHA-1 hashes of the 'instructions'
    portion of the Neurodocker dictionary.
    """
    dict_of_neurodocker_dicts = []
    for ii, params in enumerate(env_matrix):
        instructions = tuple(list_to_neurodocker_instruction(ii)
                             for ii in params)
        neurodocker_dict = instructions_to_neurodocker_specs(instructions)
        this_hash = get_dictionary_hash(neurodocker_dict['instructions'])
        dict_of_neurodocker_dicts.append((this_hash, neurodocker_dict))
    print("ENV MAT", env_matrix)
    return OrderedDict(dict_of_neurodocker_dicts)


def _generate_dockerfile(dir_, neurodocker_dict, sha1):
    """Return string representation of Dockerfile with the Neurodocker Docker
    image.
    """
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


def build_image(filepath, build_context=None, tag=None, build_opts=None):
    """Build Docker image.

    Parameters
    ----------
    filepath : path-like
        Path to Dockerfile. May be absolute or relative. If `build_context`
        if provided, `filepath` is joined to `build_context`.
    build_context : path-like
        Path to build context. If None, Docker image is built without build
        context. Dockerfile instructions that require a context
        (e.g., `ADD` and `COPY`) will fail.
    tag : str
        Docker image tag. E.g., "kaczmarj/myimage:v0.1.0".
    build_opts : str
        String of options to pass to `docker build`.
    """
    tag = '' if tag is None else "-t {}".format(tag)
    build_opts = '' if build_opts is None else build_opts

    cmd_base = "docker build {tag} {build_opts}"
    cmd = cmd_base.format(tag=tag, build_opts=build_opts)

    if build_context is not None:
        build_context = os.path.abspath(build_context)
        filepath = os.path.join(build_context, filepath)
        cmd += " -f {} {}".format(filepath, build_context)
    else:
        filepath = os.path.abspath(filepath)
        cmd += " - < {}".format(filepath)

    subprocess.run(cmd, shell=True, check=True)
