"""Object to orchestrate worflow execution."""

import itertools
import json
import os
import subprocess
import tempfile
import pdb

import container_generator as cg


class WorkflowRegtest(object):
    def __init__(self, workflow_path):
        self.workflow_path = workflow_path
        with open(os.path.join(self.workflow_path, "parameters.json")) as param_js:
            self.parameters = json.load(param_js)
        self.env_parameters = self.parameters["env"]
        self.script = os.path.join(self.workflow_path, "workflow",
                                   self.parameters["script"])
        self.command = self.parameters["command"] # TODO: adding arg
        self.tests = self.parameters["tests"] # should be a tuple (output_name, test_name)
        self.software_names, self.software_vers_gen = self.environment_map()
        self.inputs = self.parameters["inputs"]
        self.tmpdir = tempfile.TemporaryDirectory(
            prefix="tmp-workflowregtest-", dir=os.getcwd()
        )


    #TODO we double work with Jakub, should choose one
    # or at least to be sure taht the order is correct
    def environment_map(self):
        software_name =[]
        software_version = []
        for key, val in self.env_parameters.items():
            software_name.append(key)
            software_version.append(val)
        return software_name, itertools.product(*software_version)


    def testing_workflow(self):
        """run workflow for all env combination, testing for all tests"""
        with open("report_tests.txt", "w") as ft:
            ft.write("Test that fail:\n\n")

        sha_list = [key for key in self.mapping]
        for ii, software_vers in enumerate(self.matrix):
            image = "repronim/regtests:{}".format(sha_list[ii])
            self.run_cwl(image)
            #self.run_cwl("test/cwl_regtest") #TODO: for testing only

            with open("report_tests.txt", "a") as ft:
                ft.write("\n\n * Environment:\n")
                ft.write(str(software_vers))
                #for ii, soft in enumerate(self.software_names):
                #    ft.write("{}: {}\n".format(soft, software_vers[ii]))
                ft.write("\nTests:\n")
            self.run_tests()


    # TODO, just copied from Jakub example
    def generate_dockerfiles(self):
        self.matrix = cg.create_matrix_of_envs(self.parameters['env'])
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
        for sha1 in self.mapping:
            filepath = os.path.join(
                self.tmpdir.name, 'Dockerfile.{}'.format(sha1)
            )
            tag = "repronim/regtests:{}".format(sha1)
            cg.build_image(filepath, build_context=None, tag=tag)


    def run_cwl(self, image):
        self.creating_cwl(image)
        self.creating_cwl_input()
        subprocess.call(["cwl-runner", "cwl.cwl", "input.yml"])


    def creating_cwl(self, image):
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
        import testing_functions
        for (output, test) in self.tests:
            getattr(testing_functions, test)(output, os.path.join(self.workflow_path, "data_ref", output))
            # either use pytest.main() https://docs.pytest.org/en/latest/usage.html#calling-pytest-from-python-code
            # or another cwl runner
