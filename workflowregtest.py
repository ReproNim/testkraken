"""Object to orchestrate worflow execution and output tests."""

import ast
import itertools
import json, csv
import os, shutil
import subprocess
import tempfile
from collections import OrderedDict
from copy import deepcopy
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3
import pandas as pd
import ruamel.yaml
import pdb

import container_generator as cg
import cwl_generator as cwlg
from altair_plots import AltairPlots


class WorkflowRegtest(object):
    def __init__(self, workflow_path, base_dir=None):
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = os.getcwd()
        self.workflow_path = workflow_path
        self.working_dir = os.path.join(self.base_dir, os.path.basename(self.workflow_path) + "_cwl")
        os.makedirs(self.working_dir, exist_ok=True)
        with open(os.path.join(self.workflow_path, "parameters.yaml")) as param_yml:
            self.parameters = ruamel.yaml.load(param_yml)
        self.env_parameters = self.parameters["env"]
        try:
            self.plot_parameters = self.parameters["plots"]
        except KeyError:
            self.plot_parameters = []
        self.script = os.path.join(self.workflow_path, "workflow",
                                   self.parameters["script"])
        self.command = self.parameters["command"] # TODO: adding arg
        self.tests = self.parameters["tests"] # should be a tuple (output_name, test_name)
        self.inputs = self.parameters["inputs"]
        self.tmpdir = tempfile.TemporaryDirectory(
            prefix="tmp-workflowregtest-", dir=os.getcwd()
        )
        self.docker_status = []

        self._create_matrix_of_envs()
        self._create_matrix_of_string_envs()


    def _create_matrix_of_envs(self):
        """Create matrix of all combinations of environment variables.
            Create a list of short descriptions of envs as single strings"""
        self.env_spec_lists = []
        self.keys_envs = []
        for key, val in self.env_parameters.items():
            self.keys_envs.append(key)
            print("KEY< VALL", key, val)
            # val should be dictionary with options, list of dicionaries, or dictionary with "common" and "shared"
            #pdb.set_trace()
            if type(val) is list:
                self.env_spec_lists.append(val)
            elif (type(val) is dict) and (["common", "varied"] == sorted(list(val.keys()))):
                # common part should be a single dictionary, varied should be a list
                if type(val["common"]) is not dict:
                    raise Exception("common part of {} should be a dictionary".format(key))
                elif type(val["varied"]) is not list:
                    raise Exception("varied part of {} should be a list".format(key))
                # checking if common and varied have the same key
                elif any([bool(set(val["common"].keys()) & set(var_dict.keys())) for var_dict in val["varied"]]):
                    # TODO: I should probably except the situation for conda_install, pip_install and just merge two strings
                    raise Exception("common and varied parts for {} have the same key".format(key))
                else:
                    #print("TTT", [var_dict.update(val["common"]) for var_dict in val["varied"]])
                    #pdb.set_trace()
                    for var_dict in val["varied"]:
                        var_dict.update(val["common"])
                    self.env_spec_lists.append(val["varied"])
            elif type(val) is dict:
                self.env_spec_lists.append([val])
            else:
                raise Exception("value for {} has to be either list or dictionary".format(key))


        self.matrix_of_envs = list(itertools.product(*self.env_spec_lists))

         # generating a simple name for envs (gave up on including env info)
        self.env_names = ["env_{}".format(ii) for ii in range(len(self.matrix_of_envs))]


    def _testing_workflow(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file."""

        sha_list = [key for key in self.mapping]
        for ii, name in enumerate(self.env_names):
            #self.report_txt.write("\n * Environment:\n{}\n".format(software_vers))
            if self.docker_status[ii] == "docker ok":
                image = "repronim/regtests:{}".format(sha_list[ii])
                self._run_cwl(image, name)


    def _generate_docker_image(self):
        """Generate all Dockerfiles"""
        self.mapping = cg.get_dict_of_neurodocker_dicts(self.keys_envs, self.matrix_of_envs)
        os.makedirs(os.path.join(self.workflow_path, 'json'), exist_ok=True) # TODO: self.workflow_path is temporary
        for sha1, neurodocker_dict in self.mapping.items():
            try:
                print("building images: {}".format(neurodocker_dict))
                cg.docker_main(self.workflow_path, neurodocker_dict, sha1)
                self.docker_status.append("docker ok")
            except Exception as e:
                self.docker_status.append("no docker")


    def _run_cwl(self, image, soft_ver_str):
        """Running workflow with CWL"""
        cwd = os.getcwd()
        working_dir_env = os.path.join(self.working_dir, soft_ver_str)
        os.makedirs(working_dir_env, exist_ok=True)
        os.chdir(working_dir_env)
        cwl_gen = cwlg.CwlGenerator(image, soft_ver_str, self.workflow_path, self.parameters)
        cwl_gen.create_cwl()
        subprocess.call(["cwl-runner", "--no-match-user", "cwl.cwl", "input.yml"])
        os.chdir(cwd)


    def run(self):
        """The main method that runs generate all docker files, build images
            and run a workflow in all environments.
        """
        self._generate_docker_image()
        self._testing_workflow()


    def _create_matrix_of_string_envs(self):
        """creating a short string representation of various versions of software that can be used on dashboard"""
        # TODO: should probaby depend o the key, e.g. image name for base, vesiorn for fsl, for python more complicated
        _env_string_lists = []
        for (ii, key_versions) in enumerate(self.env_spec_lists):
            #pdb.set_trace()
            _env_string_lists.append(["{}: version {}".format(self.keys_envs[ii], jj) for jj in range(len(key_versions))])
            #pdb.set_trace()
            #pass

        _env_string_matrix = list(itertools.product(*_env_string_lists))

        self.env_sring_dict_matrix = []
        for env_params in _env_string_matrix:
            env_dict = {}
            for env_trs in env_params:
                key, version = env_trs.split(": ")
                env_dict[key] = version
            self.env_sring_dict_matrix.append(env_dict)


    def merging_all_output(self):
        df_el_l = []
        df_el_flat_l = []
        ii_ok = None # just to have at least one env that docker was ok
        # TODO: to jedyne miejsce z self.matric_en..
        for ii, soft_d in enumerate(self.env_sring_dict_matrix):
            #self.res_all.append(deepcopy(soft_d))
            el_dict = deepcopy(soft_d)
            el_dict["env"] = self.env_names[ii]
            if self.docker_status[ii] == "docker ok":
                ii_ok = ii
                # merging results from tests and updating self.res_all, self.res_all_flat
                df_el, df_el_flat = self._merging_test_output(el_dict, ii)
                df_el_l.append(df_el)
                df_el_flat_l.append(df_el_flat)
            else:
                el_dict["env"] = "N/A"
                df_el_l.append(pd.DataFrame(el_dict, index=[0]))
                df_el_flat_l.append(pd.DataFrame(el_dict, index=[0]))

        # TODO: not sure if I need both
        self.res_all_df = pd.concat(df_el_l).reset_index(drop=True)
        self.res_all_flat_df = pd.concat(df_el_flat_l).reset_index(drop=True)
        self.res_all_df.to_csv(os.path.join(self.working_dir, "output_all.csv"), index=False)


    def _merging_test_output(self, dict_env, ii):
        for (iir, test) in enumerate(self.tests):
            file_name = os.path.join(self.working_dir, self.env_names[ii],
                                     "report_{}.json".format(test["name"]))
            with open(file_name) as f:
                f_dict = json.load(f)
                self._checking_dict(f_dict, test["name"])
                # for some plots it's easier to use "flat" test structure
                f_dict_flat = self._flatten_dict_test(f_dict)
                if iir == 0:
                    try:
                        df_el = pd.DataFrame(f_dict)
                    except ValueError: # if results are not list
                        df_el = pd.DataFrame(f_dict, index=[0])
                    df_el_flat = pd.DataFrame(f_dict_flat, index=[0])
                else:
                    try:
                        df_el = df_el.merge(pd.DataFrame(f_dict), how="outer")
                    except ValueError: # if results are not list
                        df_el = df_el.merge(pd.DataFrame(f_dict, index=[0]), how="outer")
                    df_el_flat = pd.concat([df_el_flat, pd.DataFrame(f_dict_flat, index=[0])], axis=1)

        df_env = pd.DataFrame(dict_env, index=[0])
        df_el_flat = pd.concat([df_env, df_el_flat], axis=1)

        df_env = pd.concat([df_env] * len(df_el)).reset_index(drop=True)
        df_el = pd.concat([df_env, df_el], axis=1)

        return df_el, df_el_flat


    def _checking_dict(self, dict, test_name):
        if "index_name" in dict.keys():
            len_ind = len(dict["index_name"])
            keys_test = list(dict.keys())
            keys_test.remove("index_name")
            for key in keys_test:
                if len(dict[key]) != len_ind:
                    raise Exception ("the length for {} should be {}".format(key, len_ind))
                dict["{}:{}".format(test_name, key)] = dict.pop(key)
        else:
            keys_test = list(dict.keys())
            for key in keys_test:
                if type(dict[key]) is list:
                    raise Exception("index_name key is required if results are lists")
                else:
                    dict["{}:{}".format(test_name, key)] = dict.pop(key)
            dict["index_name"] = "N/A"


    def _flatten_dict_test(self, dict):
        if dict["index_name"] == "N/A":
            return dict
        else:
            dict_flat = {}
            for key in set(dict.keys()) - set(["index_name"]):
                for (i, el) in enumerate(dict[key]):
                    dict_flat["{}:{}".format(key, dict["index_name"][i])] = el
            return dict_flat


    def dashboard_workflow(self):
        js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples")
        for js_template in ["dashboard.js", "index.html", "style.css"]:
            shutil.copy2(os.path.join(js_dir, js_template), self.working_dir)

        ap = AltairPlots(self.working_dir, self.res_all_df, self.res_all_flat_df, self.plot_parameters)
        ap.create_plots()
