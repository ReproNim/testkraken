"""Object to orchestrate worflow execution and output tests."""

from copy import deepcopy
import dataclasses as dc
import itertools
import json, os
from pathlib import Path
import shutil
import tempfile

import pandas as pd
import yaml

import testkraken.container_generator as cg
import pydra


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
        if working_dir:
            self.working_dir = Path(working_dir).absolute()
        elif tmp_working_dir:
            self.working_dir = Path(tempfile.mkdtemp(
            prefix='testkraken-{}'.format(self.workflow_path.name))).absolute()
        else:
            raise Exception("please provide working_dir or set tmp_working_dir=Tru,"
                            "should this be implemented and use cwd??")
        self.working_dir.mkdir(parents=True, exist_ok=True)
        _validate_workflow_path(self.workflow_path)
        self.tests_dir = Path(__file__).parent / "testing_functions"
        self.build_context = self.working_dir

        with (self.workflow_path / 'parameters.yaml').open() as f:
            self._parameters = yaml.safe_load(f)
        _, new_context = _validate_parameters(self._parameters, self.workflow_path, self.tests_dir)
        if new_context:
            self.build_context = self.workflow_path
        self.data_path = self._parameters["data"]["location"]

        self._parameters.setdefault('fixed_env', [])
        if isinstance(self._parameters['fixed_env'], dict):
            self._parameters['fixed_env'] = [self._parameters['fixed_env']]
        if self._parameters.get("env", None):
            self.env_keys = list(self._parameters['env'].keys())
        else:
            self.env_keys = list(self._parameters['fixed_env'][0].keys())
        self._parameters.setdefault('plots', [])
        self.post_build = self._parameters.get("post_build", None)
        # self.framework = self._parameters.get("framework", None)
        self.docker_status = []

        self._create_matrix_of_envs()  # and _soft_vers_spec ...
        self._create_neurodocker_specs()
        self._create_matrix_of_string_envs()

         # generating a simple name for envs (gave up on including env info)
        self.env_names = ['env_{}'.format(ii) for ii, _ in enumerate(self._matrix_of_envs)]
        self.reports = {}


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
        # lists of full specification (all versions for each software/key)
        self._soft_vers_spec = {}
        for key, val in self._parameters['env'].items():
            # val should be dictionary with options, list of dictionaries,
            # or dictionary with "common" and "shared"
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
        matrix = list(itertools.product(*self._soft_vers_spec.values()))

        # Add fixed environments.
        fixed_env = deepcopy(self._parameters['fixed_env'])
        if fixed_env:
            if isinstance(fixed_env, dict):
                fixed_env = [fixed_env]
            for f in fixed_env:
                matrix.append(tuple(f[k] for k in self.env_keys))
        self._matrix_of_envs = matrix

    def _create_neurodocker_specs(self):
        self.neurodocker_specs = cg.get_dict_of_neurodocker_dicts(
            self.env_keys, self._matrix_of_envs,
            self.post_build
        )

    def _build_docker_images(self):
        """Build all Docker images."""
        print("+ building {} Docker images".format(self.nenv))
        for sha1, neurodocker_dict in self.neurodocker_specs.items():
            try:
                print("++ building image: {}".format(neurodocker_dict))
                cg.docker_main(self.working_dir, neurodocker_dict, sha1, build_context=self.build_context)
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
                self._run_pydra(image=image, soft_ver_str=name)


    def _run_pydra(self, image, soft_ver_str):
        wf = pydra.Workflow(name="wf", input_spec=["image"])#, cache_dir="/Users/dorota/testkraken/ala")
        wf.inputs.image = image

        # 1st task - analysis
        param_run = self.parameters["analysis"]
        cmd_run = [param_run["command"]]
        inp_fields_run = []
        inp_val_run = {}

        if param_run["script"]:
            script_run = param_run["script"]
            inp_fields_run.append(("script", pydra.specs.File, dc.field(
                metadata={"position": 1, "help_string": "script file", "mandatory": True,})))
            inp_val_run[f"script"] = script_run

        output_file_dict = {}
        for ind, inputs in enumerate(param_run["inputs"]):
            inputs = deepcopy(inputs)
            tp = inputs.pop("type")
            if tp == "File":
                tp = pydra.specs.File
            value = inputs.pop("value")
            name = inputs.pop("name", f"inp_{ind}")
            output_file = inputs.pop("output_file", False)
            # default values for metadata
            metadata = {"position": ind + 2,
                        "help_string": f"inp_{ind}",
                        "mandatory": True
                        }
            # updating metadata with values provided in parameters file
            metadata.update(inputs)

            field = (name, tp, dc.field(metadata=metadata))
            inp_fields_run.append(field)

            if tp is pydra.specs.File:
                inp_val_run[name] = self.data_path / value
            else:
                if output_file:
                    output_file_dict[name] = value
                    value = os.path.join("/output_pydra", value)
                inp_val_run[name] = value

        input_spec_run = pydra.specs.SpecInfo(name="Input",fields=inp_fields_run,
                                              bases=(pydra.specs.DockerSpec,))

        out_fields_run = []
        for el in self.parameters["tests"]:
            if el["file"] in output_file_dict:
                el["file"] = output_file_dict[el["file"]]
            # this would have to be modified if we allow multiple files to one test
            out_fields_run.append((f"file_{el['name']}", pydra.specs.File, el["file"]))

        output_spec_run = pydra.specs.SpecInfo(name="Output", fields=out_fields_run,
                                               bases=(pydra.specs.ShellOutSpec,))

        task_run = pydra.DockerTask(name="run", executable=cmd_run, image=wf.lzin.image,
                                    input_spec=input_spec_run, output_spec=output_spec_run,
                                    **inp_val_run)
        wf.add(task_run)

        # 2nd task - creating list from the 1st task output
        @pydra.mark.task
        @pydra.mark.annotate({"return": {"outfiles": list}})
        def outfiles_list(res):
            out_f = []
            for el in self.parameters["tests"]:
                out_f.append(res[f"file_{el['name']}"])
            return out_f

        wf.add(outfiles_list(name="outfiles", res=wf.run.lzout.all_))

        # 3rd task - tests
        input_spec_test = pydra.specs.SpecInfo(
            name="Input",
            fields=[
                ("script_test", pydra.specs.File,
                 dc.field(
                     metadata={
                         "position": 1,
                         "help_string": "test file",
                         "mandatory": True,
                     }
                 )
                 ),
                ("file_out", pydra.specs.File,
                 dc.field(
                     metadata={
                         "position": 2,
                         "help_string": "out file",
                         "argstr": "-out",
                         "mandatory": True,
                     }
                 )
                 ),
                ("file_ref", pydra.specs.File,
                 dc.field(
                     metadata={
                         "position": 3,
                         "argstr": "-ref",
                         "help_string": "out file",
                         "mandatory": True,
                     }
                 )
                 ),
                 ("name_test", str,
                 dc.field(
                     metadata={
                         "position": 4,
                         "argstr": "-name",
                         "help_string": "test name",
                         "mandatory": True,
                     }
                 )
                 ),
            ],
            bases=(pydra.specs.DockerSpec,),
        )

        output_spec_test = pydra.specs.SpecInfo(
            name="Output",
            fields=[("reports", pydra.specs.File, "report_*.json")],
            bases=(pydra.specs.ShellOutSpec,),
        )

        inp_val_test = {}
        inp_val_test["name_test"] = [el["name"] for el in self.parameters["tests"]]
        inp_val_test["script_test"] = [el["script"] for el in self.parameters["tests"]]
        inp_val_test["file_ref"] = [self.data_path / el["file"]
                                    for el in self.parameters["tests"]]

        task_test = pydra.ShellCommandTask(name="test", executable="python",
                                     input_spec=input_spec_test, output_spec=output_spec_test,
                                     file_out=wf.outfiles.lzout.outfiles,
                                     **inp_val_test).\
            split((("script_test", "name_test"), ("file_out", "file_ref")))
        wf.add(task_test)

        # setting wf output
        wf.set_output([("out", wf.run.lzout.stdout),
                       ("outfiles", wf.outfiles.lzout.outfiles),
                       ("test_out", wf.test.lzout.stdout),
                       ("reports", wf.test.lzout.reports)
                       ])
        print(f"\n running pydra workflow for {self.workflow_path} "
              f"in working directory - {self.working_dir}")
        with pydra.Submitter(plugin="cf") as sub:
            sub(wf)
        res = wf.result()
        self.reports[soft_ver_str] = res.output.reports



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
            for key in self.env_keys:
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
                    env_name=self.env_names[ii])
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

    def _merge_test_output(self, dict_env, env_name):
        """Merge test outputs."""
        for iir, test in enumerate(self._parameters['tests']):
            with self.reports[env_name][iir].open() as f:
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
    if not (p / 'scripts').is_dir():
        missing.append(('scripts', 'directory'))
    if missing:
        m = ", ".join("{} ({})".format(*ii) for ii in missing)
        raise FileNotFoundError(
            "Missing required files or directories in workflow path: {}"
            .format(m))
    return True


def _validate_input_dict(input):
    if isinstance(input, dict):
        required = {"type", "value"}
        not_found = required - set(input.keys())
        if not_found:
            raise SpecificationError(
                "Required key(s) not found in input dictionary: {}"
                    .format(', '.join(not_found)))
    else:
        raise Exception("input element has to be a dictionary")


def _validate_envs(params):
    params_env = params.get('env', None)
    params_fixedenv = params.get('fixed_env', None)
    if params_env:
        if not isinstance(params_env, dict):
            raise SpecificationError("Value of key 'env' must be a dictionary.")
        else:
            if any(not isinstance(j, (dict, list)) for j in params_env.values()):
                raise SpecificationError("Every value in 'env' must be a dictionary or list.")
            for key, val in params_env.items():
                if isinstance(val, dict) and {'common', 'varied'} == set(val.keys()):
                    if not isinstance(val['common'], dict):
                        raise SpecificationError("common part of {} should be a dictionary".format(key))
                    elif not isinstance(val['varied'], (list, tuple)):
                        raise SpecificationError("varied part of {} should be a list or tuple".format(key))
                    # checking if common and varied have the same key
                    elif any(set(val['common'].keys()).intersection(vd) for vd in val['varied']):
                        # TODO: I should probably accept when conda_install and pip_install and just merge two strings
                        raise SpecificationError("common and varied parts for {} have the same key".format(key))

    if params_fixedenv:
        if not isinstance(params_fixedenv, (dict, list)):
            raise SpecificationError("Value of key 'fixed_env' must be a dictionary or list.")
        else:
            if isinstance(params_fixedenv, dict) and params_env:
                if set(params_fixedenv.keys()) != set(params_env.keys()):
                    raise SpecificationError("Keys of 'fixed_env' must be same as keys of 'env'.")
            elif isinstance(params['fixed_env'], list):
                if params_env:
                    if any(set(f.keys()) != set(params_env.keys()) for f in params_fixedenv):
                        raise SpecificationError("Keys of 'fixed_env' must be same as keys of 'env'.")
                else:
                    if any(set(f.keys()) != set(params_fixedenv[0].keys()) for f in params_fixedenv[1:]):
                        raise SpecificationError("Keys of all environments from 'fixed_env' must be same.")


def _validate_post_build(params_postbuild):
    new_context = False
    if "copy" in params_postbuild:
        new_context = True
    # todo
    return new_context

def _validate_data(params, workflow_path):
    # TODO will be extended
    valid_types = ["workflow_path", "local"]
    if "location" not in params["data"]:
        raise Exception(f"data has to have location")
    if "type" not in params["data"] or params["data"]["type"] not in valid_types:
        raise Exception(f"data has to have type from the list {valid_types}")
    elif params["data"]["type"] == "workflow_path":
        params["data"]["location"] = workflow_path / params["data"]["location"]
    elif params["data"]["type"] == "local":
        params["data"]["location"] = Path(params["data"]["location"]).absolute()

    if not params["data"]["location"].exists():
        raise Exception(f"{params['data']['location']} doesnt exist")


def _validate_parameters(params, workflow_path, tests_path):
    """Validate parameters according to the testkraken specification."""
    required = {'analysis', 'tests'}
    not_found = required - set(params.keys())
    if "env" not in params.keys() and "fixed_env" not in params.keys():
        not_found.add("env or fixed_env")
    if not_found:
        raise SpecificationError(
            "Required key(s) not found in parameters: {}"
            .format(', '.join(not_found)))

    # Validate required parameters.
    # env and fixed_env
    _validate_envs(params)
    # checking analysis
    if not isinstance(params['analysis'], dict):
        raise SpecificationError("Value of key 'analysis' must be a dictionaries")
    else:
        analysis_script = params['analysis'].get("script", "")
        if not isinstance(analysis_script, str):
            raise SpecificationError("'script' field has to be a string")
        if analysis_script:
            analysis_script = workflow_path / 'scripts' / analysis_script
            if not analysis_script.is_file():
                raise FileNotFoundError(
                    "Script from analysis  does not exist: {}".format(analysis_script))
            else:
                params['analysis']["script"] = analysis_script
        analysis_command = params['analysis'].get("command", None)
        if not analysis_command or not isinstance(analysis_command, str):
            raise SpecificationError("'command' must be a string.")
        if not params['analysis'].get("inputs", None):
            params['analysis']["inputs"] = []
        elif not isinstance(params["analysis"]['inputs'], list):
            raise SpecificationError("Value of key 'inputs' must be a list.")
        else:
            for inp_el in params['analysis']["inputs"]:
                _validate_input_dict(inp_el)

    # checking tests
    if not isinstance(params['tests'], (list, tuple)):
        raise SpecificationError("Value of key 'tests' must be an iterable of dictionaries")
    else:
        if any(not isinstance(j, dict) for j in params['tests']):
            raise SpecificationError("Every item in 'tests' must be a dictionary.")
    for el in params['tests']:
        test_script = el.get("script", None)
        if not test_script or not isinstance(test_script, str):
            raise SpecificationError("'tests' have to have 'script' field and it has to be a str")
        if (workflow_path / 'scripts' / test_script).is_file():
            el["script"] = workflow_path / 'scripts' / test_script
        elif (tests_path / el["script"]).is_file():
            el["script"] = tests_path / el["script"]
        else:
            raise FileNotFoundError(
                "Script from test does not exist: {}".format(test_script))
    #TODO: adding checks for each of the element of tests

    # Validate optional parameters.
    new_context = None
    if params.get('post_build', None):
        new_context = _validate_post_build(params["post_build"])
    if "data" not in params:
        params["data"] = {"type": "default", "location": workflow_path / "data"}
        if not params["data"]["location"].exists():
            raise Exception(f"{params['data']['location']} doesnt exist")
    else:
        _validate_data(params, workflow_path)

    if params.get('plots', None):
        if not isinstance(params['plots'], (list, tuple)):
            raise SpecificationError("Value of key 'fixed_env' must be a dictionary.")
        else:
            if any(not isinstance(j, dict) for j in params['plots']):
                raise SpecificationError("Every item in 'plots' must be a dictionary.")

    # todo: the validation functions probably should be just members of the class,
    # todo: so don't have to return new_context, etc.
    return True, new_context


class SpecificationError(Exception):
    """Error in specification."""
    pass
