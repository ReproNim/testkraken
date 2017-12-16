"""Object to orchestrate worflow execution and output tests."""

import itertools
import json
import os
import subprocess
import tempfile
import pdb
from collections import OrderedDict

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
        #self.report_txt =  open("report_tests_{}.txt".format(
        #        os.path.basename(self.workflow_path)), "w")


    def testing_workflow(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file."""

        sha_list = [key for key in self.mapping]
        for ii, software_vers in enumerate(self.matrix):
            #self.report_txt.write("\n * Environment:\n{}\n".format(software_vers))
            image = "repronim/regtests:{}".format(sha_list[ii])
            self.run_cwl(image, software_vers)
            #self.run_tests()


    def generate_dockerfiles(self):
        """Generate all Dockerfiles"""
        self.matrix = cg.create_matrix_of_envs(self.env_parameters)
        self.mapping = cg.get_dict_of_neurodocker_dicts(self.matrix)

        os.makedirs(os.path.join(self.workflow_path, 'json'), exist_ok=True) # TODO: self.workflow_path is temporary
        try:
            for sha1, neurodocker_dict in self.mapping.items():
                print("building images: {}".format(neurodocker_dict))
                cg.generate_dockerfile(
                    self.workflow_path, neurodocker_dict, sha1
                ) # TODO: self.workflow_path is temporary
        except Exception as e:
            raise


    def build_images(self):
        """Building all docker images"""
        # TODO: self.workflow_path is temporary (should be none)
        for sha1 in self.mapping:
            filepath = os.path.join(
                self.workflow_path, 'Dockerfile.{}'.format(sha1)
            )
            tag = "repronim/regtests:{}".format(sha1)
            cg.build_image(filepath, build_context=self.workflow_path, tag=tag)


    def run_cwl(self, image, soft_ver):
        """Running workflow with CWL"""
        self.creating_main_cwl()
        self.creating_main_input(soft_ver)
        self.creating_workflow_cwl(image)
        self.creating_test_cwl()
        subprocess.call(["cwl-runner", "--no-match-user", "cwl.cwl", "input.yml"])


    def creating_workflow_cwl(self, image):
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

        cmd_cwl += "outputs:\n"

        #TODO: temporary taking ony one tests/ouptput file
        cmd_cwl += (
                "  output_files:\n"
                "    type: File\n"
                "    outputBinding:\n"
                "      glob: {}\n"
        ).format(self.tests[0][0])
        #for (ii, test_tuple) in enumerate(self.tests):
        #    cmd_cwl += (
        #        "  output_files_{}:\n"
        #        "    type: File\n"
        #        "    outputBinding:\n"
        #        "      glob: {}\n"
        #    ).format(ii, test_tuple[0])

        with open("cwl_workflow.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)

    def creating_test_cwl(self):
        cmd_cwl = (
            "# !/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: CommandLineTool\n"
            "baseCommand: python\n\n"
            "inputs:\n"
            "  script:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 1\n"
            "  input_files_out:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 2\n"
            "      prefix: -out\n"
            "  input_files_ref:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 3\n"
            "      prefix: -ref\n"
            "  input_files_report:\n"
            "    type: string\n"
            "    inputBinding:\n"
            "      position: 4\n"
            "      prefix: -report\n\n"
            "outputs:\n"
            "  output_files_report:\n"
            "    type: File\n"
            "    outputBinding:\n"
            "      glob: $(inputs.input_files_report)\n"
        )

        with open("cwl_test.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def creating_main_cwl(self):
        """Creating cwl file"""
        cmd_cwl = (
            "#!/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: Workflow\n"
            "inputs:\n"
            "  script_workf: File\n"
            "  script_test: File\n"
            "  data_ref: File\n"
            "  report_txt: string\n"
        )
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
                "  input_workf_{}: {}\n"
                ).format(ii, input_tuple[0])

        cmd_cwl += (
            "outputs:\n"
            "  testout:\n"
            "    type: File\n"
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
            "    in:\n"
            "      script: script_test\n"
            "      input_files_report: report_txt\n"
            "      input_files_out: workflow/output_files\n"
            "      input_files_ref: data_ref\n"
            "      input_files_report: report_txt\n"
            "    out: [output_files_report]"
                )

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def creating_main_input(self, soft_ver):
        """Creating input yml file for CWL"""
        soft = "_" + os.path.basename(self.workflow_path)
        for sv in soft_ver:
            soft += "_" + sv[1].split(":")[-1] #TODO, temp name of file

        cmd_in = (
            "script_workf:\n"
            "  class: File\n"
            "  path: {}\n"
            "script_test:\n"
            "  class: File\n"
            "  path: {}\n"
            "data_ref:\n"
            "  class: File\n"
            "  path: {}\n"
            "report_txt: {}\n" #TODO
        ).format(self.script,
                 os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions", self.tests[0][1]),
                 os.path.join(self.workflow_path, "data_ref", self.tests[0][0]),
                 "report_test"+soft+".txt"
                   ) # TODO: for now it's only one test possible

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
