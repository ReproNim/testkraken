"""Object to orchestrate worflow execution and output tests."""

import itertools
import json, csv
import os, shutil
import subprocess
import tempfile
import pdb
from collections import OrderedDict
from copy import deepcopy
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3
import numpy as np
import pandas as pd

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
        with open(os.path.join(self.workflow_path, "parameters.json")) as param_js:
            self.parameters = json.load(param_js, object_pairs_hook=OrderedDict)
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


    def _create_matrix_of_envs(self):
        """Create matrix of all combinations of environment variables.
            Create a list of short descriptions of envs as single strings"""
        params_as_strings = []
        for key, val in self.env_parameters.items():
            if isinstance(val, (list, tuple)):
                formatted = tuple("{}::{}".format(key, vv) for vv in val)
            else:
                formatted = tuple("{}::{}".format(key, val))
            params_as_strings.append(formatted)

        self.matrix_of_envs = list(itertools.product(*params_as_strings))

        self.soft_str = []
        for ii, specs in enumerate(self.matrix_of_envs):
            self.soft_str.append("_".join([string.split('::')[1].replace(':', '') for string in specs]))
            self.matrix_of_envs[ii] = [string.split('::') for string in specs]

        # creating additional a dictionary version
        self.matrix_envs_dict = [OrderedDict(mat) for mat in self.matrix_of_envs]



    def _testing_workflow(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file."""

        sha_list = [key for key in self.mapping]
        for ii, software_vers_str in enumerate(self.soft_str):
            #self.report_txt.write("\n * Environment:\n{}\n".format(software_vers))
            if self.docker_status[ii] == "docker ok":
                image = "repronim/regtests:{}".format(sha_list[ii])
                self._run_cwl(image, software_vers_str)


    def _generate_docker_image(self):
        """Generate all Dockerfiles"""
        self.mapping = cg.get_dict_of_neurodocker_dicts(self.matrix_of_envs)

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


    def merging_all_output(self):
        df_el_l = []
        df_el_flat_l = []
        ii_ok = None # just to have at least one env that docker was ok
        for ii, soft_d in enumerate(self.matrix_envs_dict):
            #self.res_all.append(deepcopy(soft_d))
            el_dict = deepcopy(soft_d)
            el_dict["env"] = "base-" + el_dict["base"]
            for key in self.env_parameters.keys():
                if key != "base":  # this is already included and it's always the first part
                    el_dict["env"] += "_{}-{}".format(key, el_dict[key])
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

        self.res_all_df = pd.concat(df_el_l).reset_index(drop=True)
        self.res_all_flat_df = pd.concat(df_el_flat_l).reset_index(drop=True)
        self.res_all_df.to_csv(os.path.join(self.working_dir, "output_all.csv"), index=False)


    def _merging_test_output(self, dict_env, ii):
        for (iir, test) in enumerate(self.tests):
            file_name = os.path.join(self.working_dir, self.soft_str[ii],
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
                dict["{}.{}".format(test_name, key)] = dict.pop(key)
        else:
            for key, val in dict.items():
                if type(val) is list:
                    raise Exception("index_name key is required if results are lists")
                else:
                    dict["{}.{}".format(test_name, key)] = dict.pop(key)
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

        ap = AltairPlots(self.working_dir, self.res_all_flat_df, self.plot_parameters)
        ap.create_plots()