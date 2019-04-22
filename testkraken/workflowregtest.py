"""Object to orchestrate worflow execution and output tests."""

from copy import deepcopy
import itertools
import json
import logging
import os, pdb
from pathlib import Path
import shutil
import subprocess
import tempfile

import pandas as pd
import ruamel.yaml

import testkraken.container_generator as cg
import testkraken.cwl_generator as cwlg


class WorkflowRegtest:
    """Object to test a workflow in many environments.

    Parameters
    ----------
    workflow_path: Path-like, directory of workflow.
    working_dir: Path-like, working directory, temporary directory by default.
    tmp_working_dir: Boolean value, if working_dir not provided,
        a temporary directory will be created if True

    Attributes
    ----------
    workflow_path: Path-like, directory of workflow.
    working_dir: Path-like, working directory.
    parameters: dictionary, testkraken parameters that define the workflow to
        test, the tests to use, and the environments in which to test.
    neurodocker_specs: dictionary, values are individual neurodocker
        specifications (dictionaries), and keys are the SHA-1 of the
        JSON-encoded neurodocker specifications. Tests will be run in the
        containers that are built from these neurodocker specifications.
    nenv: int, number of environments.
    """

    def __init__(self, workflow_path, working_dir=None, tmp_working_dir=False):
        self.workflow_path = Path(workflow_path).absolute()
        if working_dir and tmp_working_dir:
            raise Exception("please provide working_dir OR set tmp_working_dir=True, "
                            "do not change both arguments")
        elif tmp_working_dir:
            self.working_dir = Path(tempfile.mkdtemp(
            prefix='testkraken-{}'.format(self.workflow_path.name))).absolute()
        elif working_dir:
            self.working_dir = Path(working_dir).absolute()
            self.working_dir.mkdir(parents=True, exist_ok=True)
        else:
            # if working_dir is None and tmp_working_dir == False
            self.working_dir = (Path.cwd() / (self.workflow_path.name + "_cwl")).absolute()
            self.working_dir.mkdir(exist_ok=True)
        _validate_workflow_path(self.workflow_path)

        with (self.workflow_path / 'parameters.yaml').open() as f:
            self._parameters = ruamel.yaml.safe_load(f)

        _validate_parameters(self._parameters, self.workflow_path)

        self._parameters.setdefault('fixed_env', [])
        if isinstance(self._parameters['fixed_env'], dict):
            self._parameters['fixed_env'] = [self._parameters['fixed_env']]
        self._parameters.setdefault('inputs', [])
        self._parameters.setdefault('plots', [])
        self._parameters.setdefault('env_add', [])

        self.docker_status = []

        self._create_matrix_of_envs()  # and _soft_vers_spec ...
        self._create_neurodocker_specs()
        self._create_matrix_of_string_envs()

         # generating a simple name for envs (gave up on including env info)
        self.env_names = ['env_{}'.format(ii) for ii, _ in enumerate(self._matrix_of_envs)]

    @property
    def nenv(self):
        return len(self.neurodocker_specs)

    @property
    def parameters(self):
        return self._parameters

    def _create_matrix_of_envs(self):
        """Create matrix of all combinations of environment variables.
        Create a list of short descriptions of envs as single strings
        """
        self.keys_envs = list(self._parameters['env'].keys())  # TODO: remove
        # lists of full specification (all versions for each software/key)
        self._soft_vers_spec = {}
        for key, val in self._parameters['env'].items():
            # val should be dictionary with options, list of dictionaries, or dictionary with "common" and "shared"
            #pdb.set_trace()
            if isinstance(val, list):
                self._soft_vers_spec[key] = val
            elif isinstance(val, dict):
                if {'common', 'varied'} == set(val.keys()):
                    for var_dict in val["varied"]:
                        var_dict.update(val["common"])
                    self._soft_vers_spec[key] = val["varied"]
                else:
                    self._soft_vers_spec[key] = [val]
            else:
                raise SpecificationError(
                    "value for {} has to be either list or dictionary".format(key))
        pdb.set_trace()
        matrix = list(itertools.product(*self._soft_vers_spec.values()))

        # Add fixed environments.
        fixed_env = deepcopy(self._parameters['fixed_env'])
        if fixed_env:
            if isinstance(fixed_env, dict):
                fixed_env = [fixed_env]
            for f in fixed_env:
                matrix.append(tuple(f[k] for k in self._parameters['env'].keys()))
        self._matrix_of_envs = matrix

    def _create_neurodocker_specs(self):
        pdb.set_trace()
        self.neurodocker_specs = cg.get_dict_of_neurodocker_dicts(
            self._parameters['env'].keys(), self._matrix_of_envs, self._parameters["env_add"])

    def _build_docker_images(self):
        """Build all Docker images."""
        print("+ building {} Docker images".format(self.nenv))
        for sha1, neurodocker_dict in self.neurodocker_specs.items():
            try:
                print("++ building image: {}".format(neurodocker_dict))
                cg.docker_main(self.workflow_path, neurodocker_dict, sha1)
                pdb.set_trace()
                self.docker_status.append("docker ok")
            except Exception as e:
                self.docker_status.append(
                    "failed to build image with SHA1 {}: {}".format(sha1, e))

    def _run_workflow_in_matrix_of_envs(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file.
        """
        for name, status, sha in zip(self.env_names, self.docker_status, self.neurodocker_specs.keys()):
            if status == "docker ok":
                image = "repronim/testkraken:{}".format(sha)
                self._run_cwl(image=image, soft_ver_str=name)

    def _run_cwl(self, image, soft_ver_str):
        """Running workflow with CWL"""
        try:
            cwd = os.getcwd()
            working_dir_env = self.working_dir / soft_ver_str
            working_dir_env.mkdir(exist_ok=True)
            os.chdir(working_dir_env)
            # TODO(kaczmarj): add a directory option to CwlGenerator so we don't have to chdir.
            cwl_gen = cwlg.CwlGenerator(image, soft_ver_str, self.workflow_path, self._parameters)
            cwl_gen.create_cwl()
            subprocess.call('cwl-runner --no-match-user cwl.cwl input.yml'.split())
        except Exception:
            raise
        finally:
            os.chdir(cwd)

    def run(self):
        """The main method that runs generate all docker files, build images
            and run a workflow in all environments.
        """
        self._build_docker_images()
        self._run_workflow_in_matrix_of_envs()

    def _create_matrix_of_string_envs(self):
        """creating a short string representation of various versions of the software
        that will be used on the dashboard.
        """
        # TODO: should depend o the key? e.g. image name for base, version for fsl, for python more complicated
        self.string_softspec_dict = {}
        self.soft_vers_string = {}
        for (key, key_versions) in self._soft_vers_spec.items():
            _versions_per_key = []
            for jj, version in enumerate(key_versions):
                _versions_per_key.append("{}: version_{}".format(key, jj))
                self.string_softspec_dict["{}: version_{}".format(key, jj)] = version
            self.soft_vers_string[key] = _versions_per_key

        # creating products from dictionary
        all_keys, all_values = zip(*self.soft_vers_string.items())
        self.env_string_dict_matrix = [dict(zip(all_keys, values)) for values in itertools.product(*all_values)]

        # including info from th fixed envs
        for fixed_env in self._parameters['fixed_env']:
            _envs_versions = {}
            for key in self.keys_envs:
                # checking if the software already in self.softspec_string_dict
                if fixed_env[key] in self._soft_vers_spec[key]:
                    ind = self._soft_vers_spec[key].index(fixed_env[key])
                    _envs_versions[key] = "{}: version_{}".format(key, ind)
                else:
                    # creating a new version
                    _vers_str = "{}: version_{}".format(key, len(self._soft_vers_spec[key]))
                    self._soft_vers_spec[key].append(fixed_env[key])
                    _envs_versions[key] = _vers_str
            self.env_string_dict_matrix.append(_envs_versions)

    def merge_outputs(self):
        df_el_l = []
        df_el_flat_l = []
        for ii, soft_d in enumerate(self.env_string_dict_matrix):
            #self.res_all.append(deepcopy(soft_d))
            el_dict = deepcopy(soft_d)
            el_dict["env"] = self.env_names[ii]
            if self.docker_status[ii] == "docker ok":
                # merging results from tests and updating self.res_all, self.res_all_flat
                df_el, df_el_flat = self._merge_test_output(
                    dict_env=el_dict,
                    env_dir=self.working_dir / self.env_names[ii])
                df_el_l.append(df_el)
                df_el_flat_l.append(df_el_flat)
            else:
                el_dict["env"] = "N/A"
                df_el_l.append(pd.DataFrame(el_dict, index=[0]))
                df_el_flat_l.append(pd.DataFrame(el_dict, index=[0]))

        # TODO: not sure if I need both
        self.res_all_df = pd.concat(df_el_l).reset_index(drop=True)
        self.res_all_flat_df = pd.concat(df_el_flat_l).reset_index(drop=True)
        self.res_all_df.to_csv(self.working_dir / 'output_all.csv', index=False)

        # saving detailed describtion about the environment
        soft_vers_description = {}
        for key, val in self._soft_vers_spec.items():
            soft_vers_description[key] = [{"version": "version_{}".format(i), "description": str(spec)}
                                          for (i, spec) in enumerate(val)]
        with (self.working_dir / 'envs_descr.json').open(mode='w') as f:
            json.dump(soft_vers_description, f)

    def _merge_test_output(self, dict_env, env_dir):
        """Merge test outputs."""
        for iir, test in enumerate(self._parameters['tests']):
            with (env_dir / 'report_{}.json'.format(test['name'])).open() as f:
                report = json.load(f)
            report = _check_dict(report, test["name"])
            # for some plots it's easier to use "flat" test structure
            report_flat = _flatten_dict_test(report)
            if iir == 0:
                try:
                    df = pd.DataFrame(report)
                except ValueError: # if results are not list
                    df = pd.DataFrame(report, index=[0])
                df_flat = pd.DataFrame(report_flat, index=[0])
            else:
                try:
                    df = df.merge(pd.DataFrame(report), how="outer")
                except ValueError: # if results are not list
                    df = df.merge(pd.DataFrame(report, index=[0]), how="outer")
                df_flat = pd.concat([df_flat, pd.DataFrame(report_flat, index=[0])], axis=1)
        df_env = pd.DataFrame(dict_env, index=[0])
        df_flat = pd.concat([df_env, df_flat], axis=1)

        df_env = pd.concat([df_env] * len(df)).reset_index(drop=True)
        df = pd.concat([df_env, df], axis=1)

        return df, df_flat

    def dashboard_workflow(self):
        # copy html/js/css templates to the workflow specific directory
        js_dir = Path(__file__).absolute().parent / 'dashboard_template'
        for js_template in ["dashboard.js", "index.html", "style.css"]:
            shutil.copy2(js_dir / js_template, self.working_dir)


def _check_dict(d, test_name):
    d_nm = deepcopy(d)
    if "index_name" in d_nm.keys():
        len_ind = len(d["index_name"])
        for key, val in d.items():
            if key == 'index_name':
                continue
            if len(val) != len_ind:
                raise Exception ("the length for '{}' should be {}".format(key, len_ind))
            d_nm["{}:{}".format(test_name, key)] = d_nm.pop(key)
    else:
        for key, val in d.items():
            if isinstance(val, list):
                raise Exception("index_name key is required if results are lists")
            else:
                d_nm["{}:{}".format(test_name, key)] = d_nm.pop(key)
        d_nm["index_name"] = "N/A"
    return d_nm


def _flatten_dict_test(d):
    """Flatten dictionary of test report."""
    if d["index_name"] == "N/A":
        return d
    else:
        d_flat = {}
        for key in set(d.keys()) - {"index_name"}:
            for (i, el) in enumerate(d[key]):
                d_flat["{}:{}".format(key, d["index_name"][i])] = el
        return d_flat


def _validate_workflow_path(workflow_path):
    """Validate existence of files and directories in workflow path."""
    p = Path(workflow_path)
    missing = []
    if not (p / 'parameters.yaml').is_file():
        missing.append(('parameters.yaml', 'file'))
    if not (p / 'data_ref').is_dir():
        missing.append(('data_ref', 'directory'))
    if not (p / 'workflow').is_dir():
        missing.append(('workflow', 'directory'))
    if missing:
        m = ", ".join("{} ({})".format(*ii) for ii in missing)
        raise FileNotFoundError(
            "Missing required files or directories in workflow path: {}"
            .format(m))
    return True


def _validate_parameters(params, workflow_path):
    """Validate parameters according to the testkraken specification."""
    required = {'command', 'env', 'script', 'tests'}
    optional = {'fixed_env', 'inputs', 'plots'}

    not_found = required - set(params.keys())
    if not_found:
        raise SpecificationError(
            "Required key(s) not found in parameters: {}"
            .format(', '.join(not_found)))

    # Validate required parameters.
    if not isinstance(params['command'], str):
        raise SpecificationError("Value of key 'command' must be a string.")
    if not isinstance(params['env'], dict):
        raise SpecificationError("Value of key 'env' must be a dictionary.")
    else:
        if any(not isinstance(j, (dict, list)) for j in params['env'].values()):
            raise SpecificationError("Every value in 'env' must be a dictionary or list.")
        for k, v in params['env'].items():
            if isinstance(k, dict) and {'common', 'varied'} == set(val.keys()):
                if not isinstance(v['common'], dict):
                    raise SpecificationError("common part of {} should be a dictionary".format(key))
                elif not isinstance(v['varied'], (list, tuple)):
                    raise SpecificationError("varied part of {} should be a list or tuple".format(key))
                # checking if common and varied have the same key
                elif any(set(v['common'].keys()).intersection(vd) for vd in v['varied']):
                    # TODO: I should probably accept when conda_install and pip_install and just merge two strings
                    raise SpecificationError("common and varied parts for {} have the same key".format(k))
    if not isinstance(params['script'], str):
        raise SpecificationError("Value of key 'script' must be a string.")
    script = workflow_path / 'workflow' / params['script']
    if not script.is_file():
        raise FileNotFoundError(
            "Script in specification does not exist: {}".format(script))
    if not isinstance(params['tests'], (list, tuple)):
        raise SpecificationError("Value of key 'tests' must be an iterable of dictionaries")
    else:
        if any(not isinstance(j, dict) for j in params['tests']):
            raise SpecificationError("Every item in 'tests' must be a dictionary.")

    # Validate optional parameters.
    if params.get('fixed_env', False):
        if not isinstance(params['fixed_env'], (dict, list)):
            raise SpecificationError("Value of key 'fixed_env' must be a dictionary or list.")
        else:
            if isinstance(params['fixed_env'], dict):
                if set(params['fixed_env'].keys()) != set(params['env'].keys()):
                    raise SpecificationError("Keys of 'fixed_env' must be same as keys of 'env'.")
            elif isinstance(params['fixed_env'], list):
                if any(set(f.keys()) != set(params['env'].keys()) for f in params['fixed_env']):
                    raise SpecificationError("Keys of 'fixed_env' must be same as keys of 'env'.")
    if params.get('inputs', False):
        if not isinstance(params['inputs'], list):
            raise SpecificationError("Value of key 'inputs' must be a list.")
    if params.get('plots', False):
        if not isinstance(params['plots'], (list, tuple)):
            raise SpecificationError("Value of key 'fixed_env' must be a dictionary.")
        else:
            if any(not isinstance(j, dict) for j in params['plots']):
                raise SpecificationError("Every item in 'plots' must be a dictionary.")

    return True


class SpecificationError(Exception):
    """Error in specification."""
    pass
