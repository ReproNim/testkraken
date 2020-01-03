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
from . import check_latest_version

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
    params: dictionary, testkraken parameters that define the workflow to
        test, the tests to use, and the environments in which to test.
    neurodocker_specs: dictionary, values are individual neurodocker
        specifications (dictionaries), and keys are the SHA-1 of the
        JSON-encoded neurodocker specifications. Tests will be run in the
        containers that are built from these neurodocker specifications.
    """

    _etelemetry_version_data = None  # class variable to store etelemetry information

    def __init__(self, workflow_path, working_dir=None, tmp_working_dir=False):
        if WorkflowRegtest._etelemetry_version_data is None:
            WorkflowRegtest._etelemetry_version_data = check_latest_version()

        self.workflow_path = self.validate_workflow_path(workflow_path)
        self.working_dir = self.create_working_dir(working_dir, tmp_working_dir)

        with (self.workflow_path / "testkraken_spec.yml").open() as f:
            self.params = yaml.safe_load(f)
        self.validate_parameters()
        self.data_path = self.params["data"]["location"]

        self.create_matrix_of_envs()
        self.neurodocker_specs = cg.get_dict_of_neurodocker_dicts(
            self.matrix_of_envs, self.params["post_build"]
        )
        self.reports = {}

    def create_matrix_of_envs(self):
        """Create matrix of all combinations of environment variables.
        Create a list of short descriptions of envs as single strings
        """
        # lists of full specification (all versions for each software/key)
        self._soft_vers_spec = {}
        for key, val in self.params["env"].items():
            # val should be dictionary with options, list of dictionaries,
            # or dictionary with "common" and "shared"
            if isinstance(val, list):
                self._soft_vers_spec[key] = val
            elif isinstance(val, dict):
                if {"common", "varied"} == set(val.keys()):
                    for var_dict in val["varied"]:
                        var_dict.update(val["common"])
                    self._soft_vers_spec[key] = val["varied"]
                else:
                    self._soft_vers_spec[key] = [val]
            else:
                raise SpecificationError(
                    "value for {} has to be either list or dictionary".format(key)
                )

        envs_list = list(itertools.product(*self._soft_vers_spec.values()))
        self.matrix_of_envs = [dict(zip(self.env_keys, env)) for env in envs_list]

        _soft_str_list = [
            [f"ver_{i}" for i in range(len(el))] for el in self._soft_vers_spec.values()
        ]
        self._soft_str = dict(zip(self.env_keys, _soft_str_list))

        # Add fixed environments.
        fixed_env = deepcopy(self.params["fixed_env"])
        if fixed_env:
            if isinstance(fixed_env, dict):
                fixed_env = [fixed_env]
            for env in fixed_env:
                self.matrix_of_envs.append(env)
                for key, val in env.items():
                    if val not in self._soft_vers_spec[key]:
                        self._soft_vers_spec[key].append(val)
                        self._soft_str[key].append(f"ver_{len(self._soft_str[key])}")

        self.env_names = [
            "env_{}".format(ii) for ii, _ in enumerate(self.matrix_of_envs)
        ]

    def run(self):
        """The main method that runs generate all docker files, build images
            and run a workflow in all environments.
        """
        self._build_docker_images()
        self._run_workflow_in_matrix_of_envs()

    def _build_docker_images(self):
        """Build all Docker images."""
        print(f"+ building {len(self.neurodocker_specs)} Docker images")
        self.docker_status = []
        for sha1, neurodocker_dict in self.neurodocker_specs.items():
            try:
                print("++ building image: {}".format(neurodocker_dict))
                cg.docker_main(
                    self.working_dir,
                    neurodocker_dict,
                    sha1,
                    build_context=self.build_context,
                )
                self.docker_status.append("docker ok")
            except Exception as e:
                self.docker_status.append(
                    "failed to build image with SHA1 {}: {}".format(sha1, e)
                )

    def _run_workflow_in_matrix_of_envs(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file.
        """
        for name, status, sha in zip(
            self.env_names, self.docker_status, self.neurodocker_specs.keys()
        ):
            if status == "docker ok":
                image = "repronim/testkraken:{}".format(sha)
                self._run_pydra(image=image, soft_ver_str=name)

    def _run_pydra(self, image, soft_ver_str):
        wf = pydra.Workflow(
            name="wf", input_spec=["image"],
            cache_dir=self.working_dir,
        )
        wf.inputs.image = image

        # 1st task - analysis
        param_run = self.params["analysis"]
        cmd_run = [param_run["command"]]
        inp_fields_run = []
        inp_val_run = {}

        if param_run["script"]:
            script_run = param_run["script"]
            inp_fields_run.append(
                (
                    "script",
                    pydra.specs.File,
                    dc.field(
                        metadata={
                            "position": 1,
                            "help_string": "script file",
                            "mandatory": True,
                        }
                    ),
                )
            )
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
            metadata = {
                "position": ind + 2,
                "help_string": f"inp_{ind}",
                "mandatory": True,
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

        input_spec_run = pydra.specs.SpecInfo(
            name="Input", fields=inp_fields_run, bases=(pydra.specs.DockerSpec,)
        )

        out_fields_run = []
        for el in self.params["tests"]:
            if isinstance(el["file"], str):
                if el["file"] in output_file_dict:
                    el["file"] = output_file_dict[el["file"]]
                out_fields_run.append((f"file_{el['name']}", pydra.specs.File, el["file"]))
            elif isinstance(el["file"], list):
                for ii, file in enumerate(el["file"]):
                    out_fields_run.append((f"file_{el['name']}_{ii}", pydra.specs.File, file))
            else:
                raise Exception(f"value for file in params['tests'] has to be a str or a list")

        output_spec_run = pydra.specs.SpecInfo(
            name="Output", fields=out_fields_run, bases=(pydra.specs.ShellOutSpec,)
        )

        task_run = pydra.DockerTask(
            name="run",
            executable=cmd_run,
            image=wf.lzin.image,
            input_spec=input_spec_run,
            output_spec=output_spec_run,
            **inp_val_run,
        )
        wf.add(task_run)

        # 2nd task - creating list from the 1st task output
        @pydra.mark.task
        @pydra.mark.annotate({"return": {"outfiles": list}})
        def outfiles_list(res):
            out_f = []
            for el in self.params["tests"]:
                if isinstance(el["file"], (tuple, list)):
                    out_f.append(tuple([res[f"file_{el['name']}_{i}"] for i in range(len(el["file"]))]))
                else:
                    out_f.append(res[f"file_{el['name']}"])
            return out_f

        wf.add(outfiles_list(name="outfiles", res=wf.run.lzout.all_))

        # 3rd task - tests
        input_spec_test = pydra.specs.SpecInfo(
            name="Input",
            fields=[
                (
                    "script_test",
                    pydra.specs.File,
                    dc.field(
                        metadata={
                            "position": 1,
                            "help_string": "test file",
                            "mandatory": True,
                        }
                    ),
                ),
                (
                    "file_out",
                    (tuple, pydra.specs.File),
                    dc.field(
                        metadata={
                            "position": 2,
                            "help_string": "out file",
                            "argstr": "-out",
                            "mandatory": True,
                        }
                    ),
                ),
                (
                    "file_ref",
                    (tuple, pydra.specs.File),
                    dc.field(
                        metadata={
                            "position": 3,
                            "argstr": "-ref",
                            "help_string": "out file",
                            "mandatory": True,
                        }
                    ),
                ),
                (
                    "name_test",
                    str,
                    dc.field(
                        metadata={
                            "position": 4,
                            "argstr": "-name",
                            "help_string": "test name",
                            "mandatory": True,
                        }
                    ),
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
        inp_val_test["name_test"] = [el["name"] for el in self.params["tests"]]
        inp_val_test["script_test"] = [el["script"] for el in self.params["tests"]]
        inp_val_test["file_ref"] = []
        for el in self.params["tests"]:
            if isinstance(el["file"], str):
                inp_val_test["file_ref"].append(self.data_path / el["file"])
            elif isinstance(el["file"], list):
                inp_val_test["file_ref"].append(tuple([self.data_path / file for file in el["file"]]))


        task_test = pydra.ShellCommandTask(
            name="test",
            executable="python",
            input_spec=input_spec_test,
            output_spec=output_spec_test,
            file_out=wf.outfiles.lzout.outfiles,
            **inp_val_test,
        ).split((("script_test", "name_test"), ("file_out", "file_ref")))
        wf.add(task_test)

        # setting wf output
        wf.set_output(
            [
                ("out", wf.run.lzout.stdout),
                ("outfiles", wf.outfiles.lzout.outfiles),
                ("test_out", wf.test.lzout.stdout),
                ("reports", wf.test.lzout.reports),
            ]
        )
        print(
            f"\n running pydra workflow for {self.workflow_path} "
            f"in working directory - {self.working_dir}"
        )
        with pydra.Submitter(plugin="cf") as sub:
            sub(wf)
        res = wf.result()
        self.reports[soft_ver_str] = res.output.reports

    def merge_outputs(self):
        """ Merging all tests outputs """
        df_el_l = []
        df_el_flat_l = []
        for ii, soft_d in enumerate(self.matrix_of_envs):
            el_dict = self._soft_to_str(soft_d)
            el_dict["env"] = self.env_names[ii]
            if self.docker_status[ii] == "docker ok":
                if self.params["tests"]:
                    # merging results from tests and updating self.res_all, self.res_all_flat
                    df_el, df_el_flat = self._merge_test_output(
                        dict_env=el_dict, env_name=self.env_names[ii]
                    )
                    df_el_l.append(df_el)
                    df_el_flat_l.append(df_el_flat)
                else: # when tests not defined only env infor should be saved
                    df_env = pd.DataFrame(el_dict, index=[0])
                    df_el_l.append(df_env)
                    df_el_flat_l.append(df_env)
            else:
                el_dict["env"] = "N/A"
                df_el_l.append(pd.DataFrame(el_dict, index=[0]))
                df_el_flat_l.append(pd.DataFrame(el_dict, index=[0]))
        # TODO: not sure if I need both
        self.res_all_df = pd.concat(df_el_l).reset_index(drop=True)
        self.res_all_df.to_csv(self.working_dir / "output_all.csv", index=False)

        # saving detailed describtion about the environment
        soft_vers_description = {}
        for key, val in self._soft_vers_spec.items():
            soft_vers_description[key] = [
                {"version": "ver_{}".format(i), "description": str(spec)}
                for (i, spec) in enumerate(val)
            ]
        with (self.working_dir / "envs_descr.json").open(mode="w") as f:
            json.dump(soft_vers_description, f)

    def _soft_to_str(self, soft_dict):
        soft_dict = deepcopy(soft_dict)
        str_dict = {}
        for (key, val) in soft_dict.items():
            str_dict[key] = f"ver_{self._soft_vers_spec[key].index(val)}"
        return str_dict

    def _merge_test_output(self, dict_env, env_name):
        """Merge test outputs for one specific environment"""
        for iir, test in enumerate(self.params["tests"]):
            with self.reports[env_name][iir].open() as f:
                report = json.load(f)
            report = _check_dict(report, test["name"])
            # for some plots it's easier to use "flat" test structure
            report_flat = _flatten_dict_test(report)
            if iir == 0:
                try:
                    df = pd.DataFrame(report)
                except ValueError:  # if results are not list
                    df = pd.DataFrame(report, index=[0])
                df_flat = pd.DataFrame(report_flat, index=[0])
            else:
                try:
                    df = df.merge(pd.DataFrame(report), how="outer")
                except ValueError:  # if results are not list
                    df = df.merge(pd.DataFrame(report, index=[0]), how="outer")
                df_flat = pd.concat(
                    [df_flat, pd.DataFrame(report_flat, index=[0])], axis=1
                )

        df_env = pd.DataFrame(dict_env, index=[0])
        df_flat = pd.concat([df_env, df_flat], axis=1)
        df_env = pd.concat([df_env] * len(df)).reset_index(drop=True)
        df = pd.concat([df_env, df], axis=1)
        return df, df_flat

    def dashboard_workflow(self):
        """ Creating a simple dashboard for the results"""
        # copy html/js/css templates to the workflow specific directory
        js_dir = Path(__file__).absolute().parent / "dashboard_template"
        for js_template in ["dashboard.js", "index.html", "style.css"]:
            shutil.copy2(js_dir / js_template, self.working_dir)

    def validate_workflow_path(self, workflow_path):
        """Validate existence of files and directories in workflow path."""
        workflow_path = Path(workflow_path)

        if not workflow_path.exists():
            raise FileNotFoundError(
                f"workflow path, {self.workflow_path}, does not exist"
            )
        if not (workflow_path / "testkraken_spec.yml").is_file():
            raise FileNotFoundError(
                f"Missing required file with specification: "
                f"{self.workflow_path / 'testkraken_spec.yml'}"
            )
        return workflow_path

    def create_working_dir(self, working_dir, tmp_working_dir):
        """ creating working directory"""
        if working_dir:
            working_dir = Path(working_dir).absolute()
        elif tmp_working_dir:
            working_dir = Path(
                tempfile.mkdtemp(prefix="testkraken-{}".format(self.workflow_path.name))
            ).absolute()
        else:
            raise Exception(
                "please provide working_dir or set tmp_working_dir=Tru,"
                "should this be implemented and use cwd??"
            )
        working_dir.mkdir(parents=True, exist_ok=True)
        return working_dir

    def validate_parameters(self):
        """Validate parameters according to the testkraken specification."""

        # env and fixed_env
        self._validate_envs()
        # checking optional data and scripts
        self._validate_data()
        self._validate_scripts()
        # checking analysis
        self._validate_analysis()
        # checking tests
        self._validate_tests()

        self.params.setdefault("post_build", None)
        # if copy in post_build part that I'm changing the build_context
        if self.params["post_build"] and "copy" in self.params["post_build"]:
            self.build_context = self.workflow_path
        else:
            self.build_context = self.working_dir

        self.params.setdefault("plots", [])
        if self.params["plots"]:
            if not isinstance(self.params["plots"], (list, tuple)):
                raise SpecificationError(
                    "Value of key 'plots' must be a list or a tuple"
                )
            else:
                if any(not isinstance(j, dict) for j in self.params["plots"]):
                    raise SpecificationError(
                        "Every item in 'plots' must be a dictionary."
                    )

    def _validate_envs(self):
        """ validate the environment parts (env and fixed_env) of parameters"""
        self.params.setdefault("fixed_env", [])
        self.params.setdefault("env", None)

        if not (self.params["env"] or self.params["fixed_env"]):
            raise Exception("env or fixed_env is required")

        # checking basic types of env and fixed_env
        if self.params["env"]:
            if not isinstance(self.params["env"], dict):
                raise SpecificationError("Value of key 'env' must be a dictionary.")
            self.env_keys = list(self.params["env"].keys())
        if self.params["fixed_env"]:
            if not isinstance(self.params["fixed_env"], (list, dict)):
                raise SpecificationError(
                    "Value of key 'fixed_env' must be a dictionary or a list."
                )
            elif isinstance(self.params["fixed_env"], dict):
                self.params["fixed_env"] = [self.params["fixed_env"]]
            # if envs is not present, self.env_keys are taken from the first dictionary of fixed_env list
            if not self.params["env"]:
                self.env_keys = list(self.params["fixed_env"][0].keys())

        # checking elements of params["env"]
        if self.params["env"]:
            for key, val in self.params["env"].items():
                if not isinstance(val, (dict, list)):
                    raise SpecificationError(
                        "Every value in 'env' must be a dictionary or list."
                    )
                if isinstance(val, dict) and {"common", "varied"} == set(val.keys()):
                    if not isinstance(val["common"], dict):
                        raise SpecificationError(
                            "common part of {} should be a dictionary".format(key)
                        )
                    elif not isinstance(val["varied"], (list, tuple)):
                        raise SpecificationError(
                            "varied part of {} should be a list or tuple".format(key)
                        )
                    # checking if common and varied have the same key
                    elif any(
                        set(val["common"].keys()).intersection(vd)
                        for vd in val["varied"]
                    ):
                        # TODO: I should probably accept when conda_install and pip_install and just merge two strings
                        raise SpecificationError(
                            "common and varied parts for {} have the same key".format(
                                key
                            )
                        )

        # checking elements of params["fixed_env"]
        for env in self.params["fixed_env"]:
            if not isinstance(env, dict):
                raise SpecificationError(
                    "Each element of fixed_env list must be a dictionary."
                )
            elif set(env.keys()) != set(self.env_keys):
                raise SpecificationError(
                    "Keys of all environments from 'fixed_env' must be same."
                )
            for key, val in env.items():
                if not isinstance(val, (dict, list)):
                    raise SpecificationError(
                        "Every value in fixed_env element must be a dictionary or list."
                    )

    def _validate_data(self):
        """ validate the data part of the parameters"""
        # TODO will be extended
        if "data" in self.params:
            valid_types = ["workflow_path", "local"]
            if "location" not in self.params["data"]:
                raise Exception(f"data has to have location")
            if (
                "type" not in self.params["data"]
                or self.params["data"]["type"] not in valid_types
            ):
                raise Exception(f"data has to have type from the list {valid_types}")
            elif self.params["data"]["type"] == "workflow_path":
                self.params["data"]["location"] = (
                    self.workflow_path / self.params["data"]["location"]
                )
            elif self.params["data"]["type"] == "local":
                self.params["data"]["location"] = Path(
                    self.params["data"]["location"]
                ).absolute()
        else:
            self.params["data"] = {
                "type": "default",
                "location": self.workflow_path / "data",
            }

        if not self.params["data"]["location"].exists():
            raise Exception(f"{self.params['data']['location']} doesnt exist")

    def _validate_scripts(self):
        """ validate the data part of the parameters"""
        if "scripts" in self.params:
            self.params["scripts"] = Path(self.workflow_path) / self.params["scripts"]
        else:
            self.params["scripts"] = self.workflow_path / "scripts"
        if not self.params["scripts"].exists():
            raise Exception(f"{self.params['scripts']} doesnt exist")

    def _validate_analysis(self):
        """ validate the analysis part of the parameters"""
        if "analysis" not in self.params.keys():
            raise SpecificationError(f"analysis is a required field in parameters")
        elif not isinstance(self.params["analysis"], dict):
            raise SpecificationError("Value of key 'analysis' must be a dictionaries")
        else:
            analysis_script = self.params["analysis"].get("script", "")
            if analysis_script:
                analysis_script = self.params["scripts"] / analysis_script
                if not analysis_script.is_file():
                    raise FileNotFoundError(
                        "Script from analysis  does not exist: {}".format(
                            analysis_script
                        )
                    )
                else:
                    self.params["analysis"]["script"] = analysis_script
            else:
                self.params["analysis"]["script"] = ""
            analysis_command = self.params["analysis"].get("command", None)
            if not analysis_command or not isinstance(analysis_command, str):
                raise SpecificationError("'command' must be a string.")
            if not self.params["analysis"].get("inputs", None):
                self.params["analysis"]["inputs"] = []
            elif not isinstance(self.params["analysis"]["inputs"], list):
                raise SpecificationError("Value of key 'inputs' must be a list.")
            else:
                for inp_el in self.params["analysis"]["inputs"]:
                    self._validate_input_dict(inp_el)

    def _validate_input_dict(self, input):
        """ validate input dictionaries used in analysis"""
        if isinstance(input, dict):
            required = {"type", "value"}
            not_found = required - set(input.keys())
            if not_found:
                raise SpecificationError(
                    "Required key(s) not found in input dictionary: {}".format(
                        ", ".join(not_found)
                    )
                )
        else:
            raise Exception("input element has to be a dictionary")

    def _validate_tests(self):
        """ validate the test part of the parameters"""
        tests_path = Path(__file__).parent / "testing_functions"
        self.params.setdefault("tests", [])
        if not isinstance(self.params["tests"], (list, tuple)):
            raise SpecificationError(
                "Value of key 'tests' must be an iterable of dictionaries"
            )
        else:
            if any(not isinstance(j, dict) for j in self.params["tests"]):
                raise SpecificationError("Every item in 'tests' must be a dictionary.")
        for el in self.params["tests"]:
            test_script = el.get("script", None)
            if not test_script or not isinstance(test_script, str):
                raise SpecificationError(
                    "'tests' have to have 'script' field and it has to be a str"
                )
            if (self.params["scripts"] / test_script).is_file():
                el["script"] = self.params["scripts"] / test_script
            elif (tests_path / el["script"]).is_file():
                el["script"] = tests_path / el["script"]
            else:
                raise FileNotFoundError(
                    "Script from test does not exist: {}".format(test_script)
                )
        # TODO: adding checks for each of the element of tests


def _check_dict(d, test_name):
    d_nm = deepcopy(d)
    if "index_name" in d_nm.keys():
        len_ind = len(d["index_name"])
        for key, val in d.items():
            if key == "index_name":
                continue
            if len(val) != len_ind:
                raise Exception("the length for '{}' should be {}".format(key, len_ind))
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


class SpecificationError(Exception):
    """Error in specification."""

    pass
