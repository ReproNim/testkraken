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
        self.report_txt =  open("report_tests.txt", "w")


    def testing_workflow(self):
        """Run workflow for all env combination, testing for all tests.
        Writing environmental parameters to report text file."""
        self.report_txt.write("FAILING TESTS:\n")

        sha_list = [key for key in self.mapping]
        for ii, software_vers in enumerate(self.matrix):
            self.report_txt.write(("\n\n * Environment:\n{}\n"
                                   "Tests:\n").format(software_vers))


            image = "repronim/regtests:{}".format(sha_list[ii])
            self.run_cwl(image)
            self.run_tests()


    def generate_dockerfiles(self):
        """Generate all Dockerfiles"""
        self.matrix = cg.create_matrix_of_envs(self.env_parameters)
        self.mapping = cg.get_dict_of_neurodocker_dicts(self.matrix)

        os.mkdir(os.path.join(self.tmpdir.name, 'json'))
        try:
            for sha1, neurodocker_dict in self.mapping.items():
                print("building images: {}".format(neurodocker_dict))
                cg.generate_dockerfile(
                    self.tmpdir.name, neurodocker_dict, sha1
                )
        except Exception as e:
            raise


    def build_images(self):
        """Building all docker images"""
        for sha1 in self.mapping:
            filepath = os.path.join(
                self.tmpdir.name, 'Dockerfile.{}'.format(sha1)
            )
            tag = "repronim/regtests:{}".format(sha1)
            cg.build_image(filepath, build_context=None, tag=tag)


    def run_cwl(self, image):
        """Running workflow with CWL"""
        self.creating_cwl(image)
        self.creating_cwl_input()
        subprocess.call(["cwl-runner", "cwl.cwl", "input.yml"])


    def creating_cwl(self, image):
        """Creating cwl file"""
        cmd_cwl = (
            "#!/usr/bin/env cwl-runner\n"
            "cwlVersion: v1.0\n"
            "class: CommandLineTool\n"
            "baseCommand: {}\n"
            "hints:\n"
            "  DockerRequirement:\n"
            "    dockerPull: {}\n"
            "inputs:\n"
            "  script:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 1\n\n"
        ).format(self.command, image)

        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
                "  input_files_{}:\n"
                "    type: File\n"
                "    inputBinding:\n"
                "      position: {}\n"
                "      prefix: {}\n"
                ).format(ii, ii+2, input_tuple[0])

        cmd_cwl += "outputs:\n"

        for (ii, test_tuple) in enumerate(self.tests):
            cmd_cwl += (
                "  output_files_{}:\n"
                "    type: File\n"
                "    outputBinding:\n"
                "      glob: {}\n"
            ).format(ii, test_tuple[0])

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def creating_cwl_input(self):
        """Creating input yml file for CWL"""
        cmd_in = (
            "script:\n"
            "  class: File\n"
            "  path: {}\n"
        ).format(self.script)

        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_in += (
                "input_files_{}:\n"
                "  class: File\n"
                "  path: {}\n"
                ).format(ii, os.path.join(self.workflow_path, "data_input",
                                          input_tuple[1]))

        with open("input.yml", "w") as inp_file:
            inp_file.write(cmd_in)


    def run_tests(self):
        """Running all chosen tests for the workflow outputs"""
        import testing_functions
        for (output, test) in self.tests:
            getattr(testing_functions, test)(output, os.path.join(self.workflow_path, 
                                                                  "data_ref", output))

