"""Object to orchestrate worflow execution and output tests."""

import itertools
import json, csv
import os
import subprocess
import tempfile
import pdb
from collections import OrderedDict
from copy import deepcopy
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt, mpld3
import numpy as np

import container_generator as cg


class WorkflowRegtest(object):
    def __init__(self, workflow_path):
        self.workflow_path = workflow_path
        with open(os.path.join(self.workflow_path, "parameters.json")) as param_js:
            self.parameters = json.load(param_js, object_pairs_hook=OrderedDict)
        self.env_parameters = self.parameters["env"]
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
        self._creating_main_cwl()
        self._creating_main_input(soft_ver_str)
        self._creating_workflow_cwl(image)
        self._creating_test_cwl()
        subprocess.call(["cwl-runner", "--no-match-user", "cwl.cwl", "input.yml"])


    def _creating_workflow_cwl(self, image):
        """Creating cwl file"""
        cmd_cwl = (
            "#!/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: CommandLineTool\n"
            "baseCommand: {}\n"
            "hints:\n"
            "  DockerRequirement:\n"
            "    dockerPull: {}\n\n"
            "inputs:\n"
            "  script:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 1\n"
        ).format(self.command, image)

        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
                "  input_files_{}:\n"
                "    type: {}\n"
                "    inputBinding:\n"
                "      position: {}\n"
                "      prefix: {}\n"
                ).format(ii, input_tuple[0], ii+2, input_tuple[1])

        cmd_cwl += (
                "outputs:\n"
                "  output_files:\n"
                "    type:\n"
                "      type: array\n"
                "      items: File\n"
                "    outputBinding:\n"
                '      glob: "*.json"\n'
        )

        with open("cwl_workflow.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)

    def _creating_test_cwl(self):
        cmd_cwl = (
            "# !/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: CommandLineTool\n"
            "baseCommand: python\n\n"
            "inputs:\n"
            "  script_main:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 1\n"
            "  script_dir:\n"
            "    type: Directory\n"
            "    inputBinding:\n"
            "      position: 2\n"
            "      prefix: -dir\n"
            "  input_files_out:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 3\n"
            "      prefix: -out\n"
            "  input_dir_ref:\n"
            "    type: Directory\n"
            "    inputBinding:\n"
            "      position: 4\n"
            "      prefix: -ref\n"
            "  input_files_report:\n"
            "    type: string\n"
            "    inputBinding:\n"
            "      position: 5\n"
            "      prefix: -report\n"
            "  test_name:\n"
            "    type: string\n"
            "    inputBinding:\n"
            "      position: 6\n"
            "      prefix: -test\n\n"
            "outputs:\n"
            "  output_files_report:\n"
            "    type: File\n"
            "    outputBinding:\n"
            "      glob: $(inputs.input_files_report)\n"
        )

        with open("cwl_test.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def _creating_main_cwl(self):
        """Creating cwl file"""
        cmd_cwl = (
            "#!/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: Workflow\n"
            "requirements:\n"
            "   - class: ScatterFeatureRequirement\n"
            "inputs:\n"
            "  script_workf: File\n"
            "  script_test_main: File\n"
            "  script_test_dir: Directory\n"
            "  test_name:\n"
            "    type:\n"
            "      type: array\n"
            "      items: string\n"
            "  data_ref_dir: Directory\n"
            "  report_txt:\n"
            "    type:\n"
            "      type: array\n"
            "      items: string\n"
        )
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
            "  input_workf_{}: {}\n"
                ).format(ii, input_tuple[0])
        cmd_cwl += (
            "outputs:\n"
            "  testout:\n"
            "    type:\n"    
            "      type: array\n"
            "      items: File\n"
            "    outputSource: test/output_files_report\n\n"
            "steps:\n"
            "  workflow:\n"
            "    run: cwl_workflow.cwl\n"
            "    in:\n"
            "      script: script_workf\n"
        )
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
                "      input_files_{}: input_workf_{}\n"
            ).format(ii, ii)

        cmd_cwl += (
            "    out: [output_files]\n" #only one output per test
            "  test:\n"
            "    run: cwl_test.cwl\n"
            "    scatter: [input_files_out, test_name, input_files_report]\n"
            "    scatterMethod: dotproduct\n"
            "    in:\n"
            "      script_main: script_test_main\n"
            "      script_dir: script_test_dir\n"
            "      test_name: test_name\n"
            "      input_files_out: workflow/output_files\n"
            "      input_dir_ref: data_ref_dir\n"
            "      input_files_report: report_txt\n"
            "    out: [output_files_report]"
                )

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def _creating_main_input(self, soft_ver_str):
        """Creating input yml file for CWL"""
        test_name_l = [i[1] for i in self.tests]
        test_name_str = ('[' + len(test_name_l) * '"{}",' + ']').format(*test_name_l)

        report_str = ('[' + len(test_name_l) * '"report_{}_{}_{}.txt",'.format(
            {}, os.path.basename(self.workflow_path), soft_ver_str) + ']').format(
                    *range(len(self.tests)))

        cmd_in = (
            "script_workf:\n"
            "  class: File\n"
            "  path: {}\n"
            "script_test_main:\n"
            "  class: File\n"
            "  path: {}\n"
            "script_test_dir:\n"
            "  class: Directory\n"
            "  path: {}\n"
            "data_ref_dir:\n"
            "  class: Directory\n"
            "  path: {}\n"
            "test_name: {}\n"
             "report_txt: {}\n" #TODO
        ).format(self.script,
                 os.path.join(os.path.dirname(os.path.realpath(__file__)), "test_main.py"),
                 os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions"),
                 os.path.join(self.workflow_path, "data_ref"),
                 test_name_str,
                 report_str)
        for (ii, input_tuple) in enumerate(self.inputs):
            if input_tuple[0] == "File":
                cmd_in += (
                    "input_workf_{}:\n"
                    "  class: {}\n"
                    "  path: {}\n"
                    ).format(ii, input_tuple[0],
                             os.path.join(self.workflow_path, "data_input", input_tuple[2]))
            else:
                cmd_in += (
                    "input_workf_{}: {}\n"
                    ).format(ii, input_tuple[2])

        with open("input.yml", "w") as inp_file:
            inp_file.write(cmd_in)


    def run(self):
        """The main method that runs generate all docker files, build images
            and run a workflow in all environments.
        """
        self._generate_docker_image()
        self._testing_workflow()


    def merging_output(self):
        self.res_dict = []
        for ii, test in enumerate(self.tests):
            self.res_dict.append(OrderedDict())
            self._merging_output_test(ii)


    def _merging_output_test(self, test_id):
        # creating a list with results, each element has a dict with soft desc. and result
        self._res_list = []
        # create dictionary env: list for all env desc. (indexes from self.env_parameters),
        # and results: list of results for all env
        for key in self.env_parameters:
            self.res_dict[test_id][key] = []
        self.res_dict[test_id]["result"] = []

        for ii, soft_d in enumerate(self.matrix_envs_dict):
            el_dict = deepcopy(soft_d)
            file_name = "report_{}_{}_{}.txt".format(test_id, os.path.basename(self.workflow_path),
                                                     self.soft_str[ii])
            for k, val in soft_d.items():
                self.res_dict[test_id][k].append(self.env_parameters[k].index(val))

            if self.docker_status[ii] == "docker ok":
                with open(file_name) as f:
                    f_txt = f.read()
                    if "PASS" in f_txt:
                        el_dict["result"] = "PASS"
                        self.res_dict[test_id]["result"].append("1")
                    elif "FAIL" in f_txt:
                        el_dict["result"] = "FAIL"
                        self.res_dict[test_id]["result"].append("0")
                    else:
                         el_dict["result"] = "N/A"
                         self.res_dict[test_id]["result"].append("2")
            else:
                 el_dict["result"] = "N/A"
                 self.res_dict[test_id]["result"].append("2")
            self._res_list.append(el_dict)

        # saving merged results in one csv file
        keys_csv = self._res_list[0].keys()
        with open("{}_output_{}.csv".format(os.path.basename(self.workflow_path), test_id), 'w') as outfile:
            csv_writer = csv.DictWriter(outfile, keys_csv)
            csv_writer.writeheader()
            csv_writer.writerows(self._res_list)


    def plot_workflow_result(self):
        """plotting results, this has to be cleaned TODO"""
        nr_par = len(self.env_parameters)

        matplotlib.rcParams['xtick.labelsize'] = 10
        matplotlib.rcParams['ytick.labelsize'] = 12

        fig, ax_list = plt.subplots(nr_par, 1)

        for iid, key in enumerate(self.env_parameters):
            ax = ax_list[iid]
            res_all = []
            for ver in self.env_parameters[key]:
                x_lab = []
                res = []
                for ii, soft_d in enumerate(self.matrix_envs_dict):
                    soft_txt = ""
                    file_name = "report_test_" + os.path.basename(self.workflow_path)
                    for k, val in soft_d.items():
                        if k != key:
                            if k == "conda_env_yml":
                                soft_txt += val.replace("ironment","").replace(".yml","") + "\n"
                            else:
                                soft_txt += "{}={}\n".format(k, val.split(":")[0])
                        file_name += "_" + "".join(val.split(":"))
                    file_name += ".txt"
                    if self.docker_status[ii] == "docker ok":
                        if soft_d[key] == ver:
                            x_lab.append(soft_txt)
                            with open(file_name) as f:
                                f_txt = f.read()
                                if "PASS" in f_txt:
                                    res.append(1)
                                elif "FAIL" in f_txt:
                                    res.append(0)
                                else:
                                    res.append(2)
                    else:
                        if soft_d[key] == ver:
                            x_lab.append(soft_txt)
                            res.append(2)
                res_all.append(res)

            #TODO
            uni_val = list(set([item for sublist in res_all for item in sublist]))
            uni_val.sort()
            if uni_val == [0,1]:
                cmap = matplotlib.colors.ListedColormap(['red', 'green'])
            elif uni_val == [0,2]:
                cmap = matplotlib.colors.ListedColormap(['red', 'black'])
            elif uni_val == [1,2]:
                cmap = matplotlib.colors.ListedColormap(['green', 'black'])
            elif uni_val == [1]:
                cmap = matplotlib.colors.ListedColormap(['green'])
            elif uni_val == [0]:
                cmap = matplotlib.colors.ListedColormap(['red'])
            elif uni_val == [2]:
                cmap = matplotlib.colors.ListedColormap(['black'])
            else:
                cmap = matplotlib.colors.ListedColormap(['red', 'green', 'black'])

            print("Res_Val", res_all)
            if "env" in self.env_parameters[key][0]:
                y_lab = [val.replace("ironment", "").replace(".yml", "") + "\n" for val in self.env_parameters[key]]
            else:
                y_lab = [val.split(":")[0] for val in self.env_parameters[key]]

            c = ax.pcolor(res_all, edgecolors='b', linewidths=4, cmap=cmap)
            plt.sca(ax)
            plt.xticks([i + 0.5 for i in range(len(x_lab))], x_lab)
            plt.sca(ax)
            plt.yticks([i+0.5 for i in range(len(y_lab))],y_lab)
            ax.set_title(key, fontsize=16)


        fig.tight_layout()
        plt.savefig("fig_{}.pdf".format(os.path.basename(self.workflow_path))) 
        #mpld3.save_html(fig, "fig_{}.html".format(os.path.basename(self.workflow_path)))


    def plot_workflow_result_paralcoord(self):
        for ii, test in enumerate(self.tests): #will probably use also name later
            self._plot_workflow_result_paralcoord_test(ii)

    def _plot_workflow_result_paralcoord_test(self, test_id):
        """plotting results, this has to be cleaned TODO"""
        import pandas
        import plotly.plotly as py
        import plotly.graph_objs as go
        from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

        df = pandas.DataFrame(self.res_dict[test_id])

        list_pl = []
        for i, k in self.env_parameters.items():
            list_pl.append(dict(label=i, values=df[i], tickvals=list(range(len(k))), ticktext=k ))
        list_pl.append(dict(label="result", values=df["result"],
                            tickvals=[0, 1, 2], ticktext=["pass", "fail", "N/A"]))
        colors_d = {'0': "red", '1': "green", '2': "black"}
        my_colorscale =[]
        for ii in set(df["result"]):
            my_colorscale.append([ii, colors_d[ii]])
        line_pl = dict(color=df["result"], colorscale = my_colorscale)
        data = [go.Parcoords(line=line_pl, dimensions=list_pl)]
        layout = go.Layout(
            plot_bgcolor='#E5E5E5',
            paper_bgcolor='#E5E5E5'
        )

        fig = go.Figure(data=data, layout = layout)
        plot(fig, filename='parcoords_{}_{}'.format(os.path.basename(self.workflow_path), test_id))
