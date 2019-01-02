"""Object to orchestrate worflow execution and output tests."""

import itertools
import json
import os, shutil
import subprocess
import tempfile
from copy import deepcopy
import matplotlib
matplotlib.use('agg')
import ruamel.yaml
import pdb

import testkraken.container_generator as cg
import testkraken.cwl_generator as cwlg
from testkraken.altair_plots import AltairPlots


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
            self.parameters = ruamel.yaml.safe_load(param_yml)
        self.env_parameters = self.parameters["env"]
        self.fixed_env_parameters = self.parameters.get("fixed_env", {})
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
        if self.fixed_env_parameters:
            self._adding_fixed_envs()
        self._create_matrix_of_string_envs()

         # generating a simple name for envs (gave up on including env info)
        self.env_names = ["env_{}".format(ii) for ii in range(len(self.matrix_of_envs))]


    def _create_matrix_of_envs(self):
        """Create matrix of all combinations of environment variables.
        Create a list of short descriptions of envs as single strings
        """
        self.keys_envs = []
        # lists of full specification (all versions for each software/key)
        self.soft_vers_spec = {}
        for key, val in self.env_parameters.items():
            self.keys_envs.append(key)
            # val should be dictionary with options, list of dictionaries, or dictionary with "common" and "shared"
            if type(val) is list:
                self.soft_vers_spec[key] = val
            elif (type(val) is dict) and (["common", "varied"] == sorted(list(val.keys()))):
                # common part should be a single dictionary, varied should be a list
                if type(val["common"]) is not dict:
                    raise Exception("common part of {} should be a dictionary".format(key))
                elif type(val["varied"]) is not list:
                    raise Exception("varied part of {} should be a list".format(key))
                # checking if common and varied have the same key
                elif any([bool(set(val["common"].keys()) & set(var_dict.keys())) for var_dict in val["varied"]]):
                    # TODO: I should probably accept when conda_install and pip_install and just merge two strings
                    raise Exception("common and varied parts for {} have the same key".format(key))
                else:
                    for var_dict in val["varied"]:
                        var_dict.update(val["common"])
                    self.soft_vers_spec[key] = val["varied"]
            elif type(val) is dict:
                self.soft_vers_spec[key] = [val]
            else:
                raise Exception("value for {} has to be either list or dictionary".format(key))

        self.matrix_of_envs = list(itertools.product(*self.soft_vers_spec.values()))



    def _adding_fixed_envs(self):
        """Adding fixed env to the environments,
        all fixed envs should have the same keys as other envs
        """
        if type(self.fixed_env_parameters) is dict:
            self.fixed_env_parameters = [self.fixed_env_parameters]

        for fixed_env in self.fixed_env_parameters:
            if sorted(self.keys_envs) != sorted(list(fixed_env.keys())):
                raise Exception("fixed env should have the same keys as env")
            else:
                fixed_env_spec = []
                for key in self.keys_envs:
                    fixed_env_spec.append(fixed_env[key])
            self.matrix_of_envs.append(tuple(fixed_env_spec))


    def _testing_workflow(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file.
        """
        sha_list = [key for key in self.mapping]
        for ii, name in enumerate(self.env_names):
            #self.report_txt.write("\n * Environment:\n{}\n".format(software_vers))
            if self.docker_status[ii] == "docker ok":
                image = "repronim/regtests:{}".format(sha_list[ii])
                self._run_cwl(image, name)


    def _generate_docker_image(self):
        """Generate all Dockerfiles"""
        self.mapping = cg.get_dict_of_neurodocker_dicts(self.keys_envs, self.matrix_of_envs)
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
        """creating a short string representation of various versions of the software
        that will be used on the dashboard.
        """
        # TODO: should depend o the key? e.g. image name for base, version for fsl, for python more complicated
        self.string_softspec_dict = {}
        self.soft_vers_string = {}
        for (key, key_versions) in self.soft_vers_spec.items():
            _versions_per_key = []
            for jj, version in enumerate(key_versions):
                _versions_per_key.append("{}: version_{}".format(key, jj))
                self.string_softspec_dict["{}: version_{}".format(key, jj)] = version
            self.soft_vers_string[key] = _versions_per_key

        # creating products from dictionary
        all_keys, all_values = zip(*self.soft_vers_string.items())
        self.env_sring_dict_matrix = [dict(zip(all_keys, values)) for values in itertools.product(*all_values)]

        # including info from th fixed envs
        for fixed_env in self.fixed_env_parameters:
            _envs_versions = {}
            for key in self.keys_envs:
                # checking if the software already in self.softspec_string_dict
                if fixed_env[key] in self.soft_vers_spec[key]:
                    ind = self.soft_vers_spec[key].index(fixed_env[key])
                    _envs_versions[key] = "{}: version_{}".format(key, ind)
                else:
                    # creating a new version
                    _vers_str = "{}: version_{}".format(key, len(self.soft_vers_spec[key]))
                    self.soft_vers_spec[key].append(fixed_env[key])
                    _envs_versions[key] = _vers_str
            self.env_sring_dict_matrix.append(_envs_versions)


    def merging_all_output(self):
        df_el_l = []
        df_el_flat_l = []
        for ii, soft_d in enumerate(self.env_sring_dict_matrix):
            #self.res_all.append(deepcopy(soft_d))
            el_dict = deepcopy(soft_d)
            el_dict["env"] = self.env_names[ii]
            if self.docker_status[ii] == "docker ok":
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

        # saving detailed describtion about the environment
        soft_vers_description = {}
        for key, val in self.soft_vers_spec.items():
            soft_vers_description[key] = [{"version": "version_{}".format(i), "description": str(spec)}
                                          for (i, spec) in enumerate(val)]
        with open(os.path.join(self.working_dir, "envs_descr.json"), "w") as f:
            json.dump(soft_vers_description, f)


    def _merging_test_output(self, dict_env, ii):
        """merging all test outputs"""
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
        """flattening the dictionary"""
        if dict["index_name"] == "N/A":
            return dict
        else:
            dict_flat = {}
            for key in set(dict.keys()) - {"index_name"}:
                for (i, el) in enumerate(dict[key]):
                    dict_flat["{}:{}".format(key, dict["index_name"][i])] = el
            return dict_flat


    def dashboard_workflow(self):
        # copy html/js/css templates to the workflow specific directory
        js_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard_template")
        for js_template in ["dashboard.js", "index.html", "style.css"]:
            shutil.copy2(os.path.join(js_dir, js_template), self.working_dir)
        # adding altair plots #TODO: move to js?
        ap = AltairPlots(self.working_dir, self.res_all_df, self.res_all_flat_df, self.plot_parameters)
        ap.create_plots()
