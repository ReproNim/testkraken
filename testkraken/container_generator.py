"""Methods to generate Dockerfiles with Neurodocker."""

import copy
import hashlib
import json
import os
import subprocess
from collections import OrderedDict
import pdb

NEURODOCKER_IMAGE = 'kaczmarj/neurodocker:testkraken@sha256:8979fc47673a30826f4bf1c11cfb87d78b919ba16bf11ad6cb2d0b653c57832c'


def _instructions_to_neurodocker_specs(keys, env_spec, env_add):
    """Return dictionary compatible with Neurodocker given a list of
    instructions.

    Parameters
    ----------
    keys: list of strings. 'base' must be included.
    env_spec: list or tuple of dictionaries. Each dictionary is the
        specification for a single environment.

    Returns
    -------
    A dictionary compatible with Neurodocker.
    """
    env_spec = copy.deepcopy(env_spec)
    instructions = []
    if "base" not in keys:
        raise ValueError("base image has to be provided")

    for ii, key in enumerate(keys):
        # pdb.set_trace()
        if key == "base":
            base_image = env_spec[ii].get('image', None)
            if base_image is None:
                raise Exception("image has to be provided in base")
            this_instruction = ('base', base_image)
            if 'pkg_manager' not in env_spec[ii].keys():
                pkg_manager = 'apt'  # assume apt
                for img in {'centos', 'fedora'}:
                    if img in base_image:
                        pkg_manager = 'yum'
            else:
                pkg_manager = env_spec[ii]['pkg_manager']
        elif key == "miniconda":
            # Copy yaml environment file into the container.
            if 'yaml_file' in env_spec[ii].keys():
                instructions.append(
                    ('copy', (env_spec[ii]['yaml_file'], env_spec[ii]['yaml_file'])))
            env_spec[ii].setdefault('create_env', 'testkraut')
            env_spec[ii].setdefault('activate', True)
            this_instruction = (key, env_spec[ii])
        elif key in ["fsl", "afni"]:
            this_instruction = (key, env_spec[ii])
        elif key == "copy":
            pdb.set_trace()
            this_instruction = (key, env_spec[ii])
        else:
            raise Exception("key has to be base, miniconda or fsl")
        instructions.append(this_instruction)
    if env_add:
        for key, val in env_add.items():
            if key == "copy":
                this_instruction = (key, val)
            instructions.append(this_instruction)
    pdb.set_trace()
    return {
        "pkg_manager": pkg_manager,
        "instructions": tuple(instructions),
    }


def _get_dictionary_hash(d):
    """Return SHA-1 hash of dictionary `d`. The dictionary is JSON-encoded
    prior to getting the hash value.
    """
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()


def get_dict_of_neurodocker_dicts(env_keys, env_matrix, env_add=None):
    """Return dictionary of Neurodocker specifications.

    Parameters
    ----------
    env_keys: list of keys in the environment. Must include 'base'.
    env_matrix: list of dictionary, where each dictionary specifies an environment.
        Each dictionary must contain the keys in `env_keys`.

    Returns
    -------
    Ordered dictionary of Neurodocker specifications. The keys in this dictionary are the
    sha1 values for the JSON-encoded dictionaries, and the values are the corresponding
    dictionaries.
    """
    d = []
    for ii, params in enumerate(env_matrix):
        neurodocker_dict = _instructions_to_neurodocker_specs(env_keys, params, env_add)
        this_hash = _get_dictionary_hash(neurodocker_dict['instructions'])
        d.append((this_hash, neurodocker_dict))
    pdb.set_trace()
    return OrderedDict(d)


def generate_dockerfile(neurodocker_dict):
    """Return string representation of Dockerfile, made with Neurodocker
    Docker image.
    """
    cmd = "docker run --rm -i -a stdin -a stdout {image} generate docker -"
    cmd = cmd.format(image=NEURODOCKER_IMAGE)
    pdb.set_trace()
    neurodcoker dict wyglada dla mnie dobrze, ale nie dziala
    moze powinnam przejsc najpierw do najnowszego neurodockera
    output = subprocess.run(
        cmd.split(),
        input=json.dumps(neurodocker_dict).encode(),
        check=True,
        stdout=subprocess.PIPE).stdout.decode()
    pdb.set_trace()
    return output


def write_dockerfile(neurodocker_dict, filepath):
    """Generate and write Dockerfile to `filepath`."""
    dockerfile = generate_dockerfile(neurodocker_dict)

    with open(filepath, 'w') as fp:
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
    filepath = os.path.abspath(filepath)

    if build_context is not None:
        build_context = os.path.abspath("build_context)
        cmd += " -f {} {}".format(filepath, build_context)
        input = None
    else:
        with open(filepath) as f:
            input = f.read()
        cmd += " -"

    subprocess.run(cmd.split(), check=True, input=input)


def docker_main(workflow_path, neurodocker_dict, sha1):
    filepath = os.path.join(workflow_path, 'Dockerfile.{}'.format(sha1))
    pdb.set_trace()
    write_dockerfile(neurodocker_dict=neurodocker_dict, filepath=filepath)
    pdb.set_trace()
    tag = "repronim/testkraken:{}".format(sha1)
    build_image(filepath, build_context=workflow_path, tag=tag)
