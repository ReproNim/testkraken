import os, pdb
import ruamel.yaml


class CwlGenerator(object):
    def __init__(self, image, soft_ver_str, path, parameters):
        self.image = image
        self.soft_ver_str = soft_ver_str
        self.workflow_path = path
        self.script = os.path.join(self.workflow_path, "workflow",
                                   parameters["script"])
        self.command = parameters["command"]
        self.tests = parameters["tests"]
        self.inputs = parameters["inputs"]
        #TODO clean it
        self.tests_name = ["{}".format(test["name"]) for test in self.tests]
        self.tests_file_l = []
        self.output_files_tests_l = []
        self.workflow_output_files_tests_l = []
        self.data_ref_l = []
        for it, test in enumerate(self.tests):
            if type(test["file"]) is str:
                test["file"] = [test["file"]]
            self.tests_file_l.append(test["file"])
            self.output_files_tests_l.append("output_files_tests_{}".format(it))
            self.workflow_output_files_tests_l.append("workflow/output_files_tests_{}".format(it))
            self.data_ref_l.append("data_ref_{}".format(it))


    def create_cwl(self):
        self._creating_main_cwl()
        self._creating_main_input() # should be in __init__?
        self._creating_workflow_cwl()
        self._creating_tests_cwl()


    def _creating_workflow_cwl(self):
        """Creating cwl file"""
        cmd_cwl = {}
        cmd_cwl["cwlVersion"] = "v1.0"
        cmd_cwl["class"] = "CommandLineTool"
        cmd_cwl["baseCommand"] = self.command
        cmd_cwl["hints"] = {}
        cmd_cwl["hints"]["DockerRequirement"] = {}
        cmd_cwl["hints"]["DockerRequirement"]["dockerPull"] = self.image

        cmd_cwl["inputs"] = {}
        cmd_cwl["inputs"]["script"] = {}
        cmd_cwl["inputs"]["script"]["type"] = "File"
        cmd_cwl["inputs"]["script"]["inputBinding"] = {}
        cmd_cwl["inputs"]["script"]["inputBinding"]["position"] = 1

        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl["inputs"]["input_files_{}".format(ii)] = {}
            cmd_cwl["inputs"]["input_files_{}".format(ii)]["type"] = input_tuple[0]
            cmd_cwl["inputs"]["input_files_{}".format(ii)]["inputBinding"] = {}
            cmd_cwl["inputs"]["input_files_{}".format(ii)]["inputBinding"]["position"] = ii + 2
            # TODO: it should be changed (using dict instead of list?)
            if input_tuple[1]:
                cmd_cwl["inputs"]["input_files_{}".format(ii)]["inputBinding"]["prefix"] = input_tuple[1]


        cmd_cwl["outputs"] = {}
        for (it, test) in enumerate(self.tests):
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)] = {}
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)]["type"] = {}
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)]["type"]["type"] = "array"
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)]["type"]["items"] = "File"
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)]["outputBinding"] = {}
            cmd_cwl["outputs"]["output_files_tests_{}".format(it)]["outputBinding"]["glob"] = self.tests_file_l[it]

        with open("cwl_workflow.cwl", "w") as cwl_file:
            print("# !/usr/bin/env cwl-runner", file=cwl_file)
            print(ruamel.yaml.dump(cmd_cwl), file=cwl_file)


    def _creating_tests_cwl(self):
        cmd_cwl = {}
        cmd_cwl["cwlVersion"] = "v1.0"
        cmd_cwl["class"] = "CommandLineTool"
        cmd_cwl["baseCommand"] = "python"

        cmd_cwl["inputs"] = {}
        cmd_cwl["inputs"]["script"] = {}
        cmd_cwl["inputs"]["script"]["type"] = "File"
        cmd_cwl["inputs"]["script"]["inputBinding"] = {}
        cmd_cwl["inputs"]["script"]["inputBinding"]["position"] = 1

        cmd_cwl["inputs"]["input_files_out"] = {}
        cmd_cwl["inputs"]["input_files_out"]["type"] = {}
        cmd_cwl["inputs"]["input_files_out"]["type"]["type"] = "array"
        cmd_cwl["inputs"]["input_files_out"]["type"]["items"] = "File"
        cmd_cwl["inputs"]["input_files_out"]["inputBinding"] = {}
        cmd_cwl["inputs"]["input_files_out"]["inputBinding"]["position"] = 3
        cmd_cwl["inputs"]["input_files_out"]["inputBinding"]["prefix"] = "-out"

        cmd_cwl["inputs"]["input_ref"] = {}
        cmd_cwl["inputs"]["input_ref"]["type"] = {}
        cmd_cwl["inputs"]["input_ref"]["type"]["type"] = "array"
        cmd_cwl["inputs"]["input_ref"]["type"]["items"] = "File"
        cmd_cwl["inputs"]["input_ref"]["inputBinding"] = {}
        cmd_cwl["inputs"]["input_ref"]["inputBinding"]["position"] = 4
        cmd_cwl["inputs"]["input_ref"]["inputBinding"]["prefix"] = "-ref"

        cmd_cwl["inputs"]["name"] = {}
        cmd_cwl["inputs"]["name"]["type"] = "string"
        cmd_cwl["inputs"]["name"]["inputBinding"] = {}
        cmd_cwl["inputs"]["name"]["inputBinding"]["position"] = 5
        cmd_cwl["inputs"]["name"]["inputBinding"]["prefix"] = "-name"

        cmd_cwl["outputs"] = {}
        cmd_cwl["outputs"]["output_files_report"] = {}
        cmd_cwl["outputs"]["output_files_report"]["type"] = "File"
        cmd_cwl["outputs"]["output_files_report"]["outputBinding"] = {}
        cmd_cwl["outputs"]["output_files_report"]["outputBinding"]["glob"] = "report_*.json"

        with open("cwl_tests.cwl", "w") as cwl_file:
            print("# !/usr/bin/env cwl-runner", file=cwl_file)
            print(ruamel.yaml.dump(cmd_cwl), file=cwl_file)


    def _creating_main_cwl(self):
        """Creating cwl file"""
        cmd_cwl = {}
        cmd_cwl["cwlVersion"] = "v1.0"
        cmd_cwl["class"] = "Workflow"
        cmd_cwl["requirements"] = [{"class": "ScatterFeatureRequirement"},
                                   {"class": "MultipleInputFeatureRequirement"}]


        cmd_cwl["inputs"] = {}
        cmd_cwl["inputs"]["script_workf"] = "File"
        cmd_cwl["inputs"]["script_tests"] = {}
        cmd_cwl["inputs"]["script_tests"]["type"] = {}
        cmd_cwl["inputs"]["script_tests"]["type"]["type"] = "array"
        cmd_cwl["inputs"]["script_tests"]["type"]["items"] = "File"
        cmd_cwl["inputs"]["name_tests"] = {}
        cmd_cwl["inputs"]["name_tests"]["type"] = {}
        cmd_cwl["inputs"]["name_tests"]["type"]["type"] = "array"
        cmd_cwl["inputs"]["name_tests"]["type"]["items"] = "string"
        for (it, test) in enumerate(self.tests):
            cmd_cwl["inputs"]["data_ref_{}".format(it)] = {}
            cmd_cwl["inputs"]["data_ref_{}".format(it)]["type"] = {}
            cmd_cwl["inputs"]["data_ref_{}".format(it)]["type"]["type"] = "array"
            cmd_cwl["inputs"]["data_ref_{}".format(it)]["type"]["items"] = "File"
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl["inputs"]["input_workf_{}".format(ii)] = {}
            cmd_cwl["inputs"]["input_workf_{}".format(ii)]["type"] = input_tuple[0]


        cmd_cwl["outputs"] = {}
        cmd_cwl["outputs"]["tests_rep"] = {}
        cmd_cwl["outputs"]["tests_rep"]["type"] = {}
        cmd_cwl["outputs"]["tests_rep"]["type"]["type"] = "array"
        cmd_cwl["outputs"]["tests_rep"]["type"]["items"] = "File"
        cmd_cwl["outputs"]["tests_rep"]["outputSource"] = "tests/output_files_report"

        cmd_cwl["steps"] = {}
        cmd_cwl["steps"]["workflow"] = {}
        cmd_cwl["steps"]["workflow"]["run"] = "cwl_workflow.cwl"
        cmd_cwl["steps"]["workflow"]["in"] = {}
        cmd_cwl["steps"]["workflow"]["in"]["script"] = "script_workf"
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl["steps"]["workflow"]["in"]["input_files_{}".format(ii)] = "input_workf_{}".format(ii)
        cmd_cwl["steps"]["workflow"]["out"] = self.output_files_tests_l

        cmd_cwl["steps"]["tests"] = {}
        cmd_cwl["steps"]["tests"]["run"] = "cwl_tests.cwl"
        cmd_cwl["steps"]["tests"]["scatter"] = ["input_files_out", "script", "input_ref", "name"]
        cmd_cwl["steps"]["tests"]["scatterMethod"] = "dotproduct"
        cmd_cwl["steps"]["tests"]["in"] = {}
        cmd_cwl["steps"]["tests"]["in"]["script"] = "script_tests"
        cmd_cwl["steps"]["tests"]["in"]["input_files_out"] = {}
        cmd_cwl["steps"]["tests"]["in"]["input_files_out"]["source"] = self.workflow_output_files_tests_l
        cmd_cwl["steps"]["tests"]["in"]["input_files_out"]["linkMerge"] = "merge_nested"
        cmd_cwl["steps"]["tests"]["in"]["input_ref"] = {}
        cmd_cwl["steps"]["tests"]["in"]["input_ref"]["source"] = self.data_ref_l
        cmd_cwl["steps"]["tests"]["in"]["input_ref"]["linkMerge"] = "merge_nested"
        cmd_cwl["steps"]["tests"]["in"]["name"] = "name_tests"
        cmd_cwl["steps"]["tests"]["out"] = ["output_files_report"]

        with open("cwl.cwl", "w") as cwl_file:
            print("# !/usr/bin/env cwl-runner", file=cwl_file)
            print(ruamel.yaml.dump(cmd_cwl), file=cwl_file)

    def _creating_main_input(self):
        """Creating input yml file for CWL"""
        cmd_in = {}
        cmd_in["script_workf"] = {}
        cmd_in["script_workf"]["class"] = "File"
        cmd_in["script_workf"]["path"] = self.script
        cmd_in["script_tests"] = []
        for test in self.tests:
            cmd_in["script_tests"].append(
                {"class": "File",
                 "path": os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions",test["script"])}
            )
        for it, test in enumerate(self.tests):
            cmd_in["data_ref_{}".format(it)] = []
            for file in list(test["file"]):
                cmd_in["data_ref_{}".format(it)].append(
                    {"class": "File",
                     "path": os.path.join(self.workflow_path, "data_ref", file)}
                )
        for (ii, input_tuple) in enumerate(self.inputs):
            if input_tuple[0] == "File":
                cmd_in["input_workf_{}".format(ii)] = {}
                cmd_in["input_workf_{}".format(ii)]["class"] = input_tuple[0]
                cmd_in["input_workf_{}".format(ii)]["path"] = os.path.join(self.workflow_path, "data_input", input_tuple[2])
            elif input_tuple[0] == "int":
                cmd_in["input_workf_{}".format(ii)] = int(input_tuple[2])
            elif input_tuple[0] == "float":
                cmd_in["input_workf_{}".format(ii)] = float(input_tuple[2])
            else:
                cmd_in["input_workf_{}".format(ii)] = input_tuple[2]

        cmd_in["name_tests"] = self.tests_name

        with open("input.yml", "w") as inp_file:
            print(ruamel.yaml.dump(cmd_in), file=inp_file)