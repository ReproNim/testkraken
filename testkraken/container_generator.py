"""Methods to generate Dockerfiles with Neurodocker."""

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
from collections import OrderedDict
from neurodocker.neurodocker import main as nrd_main
import neurodocker as ndr

# default setting for specific neurodocker keys,
# this value will not have to be set in the parameters.yml, but can be overwritten
DEFAULT_INSTRUCTIONS = {"miniconda": {"create_env": "testkraken", "activate": True}}
# all keys allowed by neurodocker for Docker
VALID_DOCKER_KEYS = ndr.Dockerfile._implementations.keys()


def _instructions_to_neurodocker_specs(env_spec):
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
    if "base" not in env_spec.keys():
        raise ValueError("base image has to be provided")

    for key, val in env_spec.items():
        if key == "base":
            base_image = val.get("image", None)
            if base_image is None:
                raise Exception("image has to be provided in base")
            this_instruction = ("base", base_image)
            if "pkg_manager" not in val.keys():
                pkg_manager = "apt"  # assume apt
                for img in {"centos", "fedora"}:
                    if img in base_image:
                        pkg_manager = "yum"
            else:
                pkg_manager = val["pkg_manager"]
        elif key in VALID_DOCKER_KEYS:
            key_spec = copy.deepcopy(DEFAULT_INSTRUCTIONS.get(key, {}))
            key_spec.update(val)
            this_instruction = (key, key_spec)
        else:
            raise Exception(
                f"{key} is not a valid key, must be "
                f"from the list {VALID_DOCKER_KEYS}"
            )
        instructions.append(this_instruction)
    return {"pkg_manager": pkg_manager, "instructions": tuple(instructions)}


def _get_dictionary_hash(d):
    """Return SHA-1 hash of dictionary `d`. The dictionary is JSON-encoded
    prior to getting the hash value.
    """
    return hashlib.sha1(json.dumps(d, sort_keys=True).encode()).hexdigest()


def get_dict_of_neurodocker_dicts(env_matrix, post_build=None):
    """Return dictionary of Neurodocker specifications.

    Parameters
    ----------
    env_keys: list of keys in the environment. Must include 'base'.
    env_matrix: list of dictionary, where each dictionary specifies an environment.
        Each dictionary must contain the keys in `env_keys`.
    framework: optional, can be nfm

    Returns
    -------
    Ordered dictionary of Neurodocker specifications. The keys in this dictionary are the
    sha1 values for the JSON-encoded dictionaries, and the values are the corresponding
    dictionaries.
    """
    nrd_dict = []
    for params in env_matrix:
        neurodocker_dict = _instructions_to_neurodocker_specs(params)
        this_hash = _get_dictionary_hash(neurodocker_dict["instructions"])
        if (this_hash, neurodocker_dict) in nrd_dict:
            raise Exception(
                "two identical environment specifications are found, "
                "remove one parameters.yml file"
            )
        # if framework provided the neurodocker_dict should be updated
        if post_build:
            neurodocker_dict = _post_build(neurodocker_dict, post_build)
        nrd_dict.append((this_hash, neurodocker_dict))
    return OrderedDict(nrd_dict)


def _post_build(neurodocker_dict, post_build):
    """ extra instructions for the nfm framework"""
    instr_list = list(neurodocker_dict["instructions"])
    for key, val in post_build.items():
        if key == "miniconda":
            env_nm = None
            for i, el in enumerate(instr_list):
                if el[0] == "miniconda":
                    env_nm = el[1]["create_env"]
            if env_nm:
                miniconda_dict = {"use_env": env_nm}
            else:
                miniconda_dict = {"create_env": "testkraken"}
            miniconda_dict.update(val)
            instr_list.append(("miniconda", miniconda_dict))
        else:
            instr_list.append((key, val))
    neurodocker_dict["instructions"] = tuple(instr_list)
    return neurodocker_dict


def write_dockerfile(nrd_jsonfile, dockerfile):
    """ Generate and write Dockerfile to `dockerfile`, uses Neurodocker library
        This doesn't work, since nrd_main changes nrd attributes,
        using write_dockerfile_sp for now
    """
    nrd_args = [
        "generate",
        "docker",
        nrd_jsonfile,
        "-o",
        dockerfile,
        "--no-print",
        "--json",
    ]
    # not sure if I need to use out_json anywhere, might remove "--json"
    out_json = nrd_main(nrd_args)


def write_dockerfile_sp(nrd_jsonfile, dockerfile):
    """ Generate and write Dockerfile to `dockerfile`, uses Neurodocker cli
        These is a tmp function, would prefer to use write_dockerfile
    """
    nrd_args = [
        "neurodocker",
        "generate",
        "docker",
        nrd_jsonfile,
        "-o",
        dockerfile,
        "--no-print",
        "--json",
    ]
    # not sure if I need to use out_json anywhere, might remove "--json"
    out_json = subprocess.run(
        nrd_args, check=True, stdout=subprocess.PIPE
    ).stdout.decode()


def build_image(dockerfile, build_context=None, tag=None, build_opts=None):
    """Build Docker image.

    Parameters
    ----------
    dockerfile : path-like
        Path to Dockerfile. May be absolute or relative. If `build_context`
        if provided, `dockerfile` is joined to `build_context`.
    build_context : path-like
        Path to build context. If None, Docker image is built without build
        context. Dockerfile instructions that require a context
        (e.g., `ADD` and `COPY`) will fail.
    tag : str
        Docker image tag. E.g., "kaczmarj/myimage:v0.1.0".
    build_opts : str
        String of options to pass to `docker build`.
    """
    tag = "" if tag is None else "-t {}".format(tag)
    build_opts = "" if build_opts is None else build_opts

    cmd_base = "docker build {tag} {build_opts}"
    cmd = cmd_base.format(tag=tag, build_opts=build_opts)
    dockerfile = os.path.abspath(dockerfile)
    if build_context is not None:
        build_context = os.path.abspath(build_context)
        # changing build directory, needed for fnp
        # was failing wit providing build_context to build command)
        cwd = os.getcwd()
        os.chdir(build_context)
        cmd += " -f {} .".format(dockerfile)
        input = None
    else:
        with open(dockerfile) as f:
            input = f.read()
        cmd += " -"
    subprocess.run(cmd.split(), check=True, input=input)
    if build_context is not None:
        os.chdir(cwd)


def docker_main(workflow_dir, neurodocker_dict, sha1, build_context=None):
    dockerfile = os.path.join(workflow_dir, "Dockerfile.{}".format(sha1))
    jsonpath = os.path.join(workflow_dir, f"nrd_spec_{sha1}.json")
    with open(jsonpath, "w") as fj:
        json.dump(neurodocker_dict, fj)
    if not Path(dockerfile).exists():
        write_dockerfile_sp(nrd_jsonfile=jsonpath, dockerfile=dockerfile)
    tag = "repronim/testkraken:{}".format(sha1)
    build_image(dockerfile, build_context=build_context, tag=tag)
