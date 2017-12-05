import os, subprocess, json
import itertools
import pdb

Workflow_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)),  "workflows4regtests", "basic_examples",)

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


    def environment_map(self):
        software_name =[]
        software_version = []
        for key, val in self.env_parameters.items():
            software_name.append(key)
            software_version.append(val)
        return software_name, itertools.product(*software_version)


    def testing_workflow(self):
        """run workflow for all env combination, testing for all tests"""
        for software_vers in self.software_vers_gen:
            dockerfile = self.calling_neurodocker(software_vers)
            image = self.building_image(dockerfile)
            self.run_cwl("test/cwl_regtest") #TODO: for testing only
            self.run_tests()

    # TODO
    def building_image(self, dockerfile):
        pass

        
    def calling_neurodocker(self, software_vers):
        #use self.software_names
        pass
    
    def run_cwl(self, image):
        self.creating_cwl(image)
        self.creating_cwl_input()
        subprocess.call(["cwl-runner", "cwl.cwl", "input.yml"])


    def creating_cwl(self, image):
        cmd_cwl = ("#!/usr/bin/env cwl-runner\n"
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
        "outputs: []\n").format(self.command, image) #TODO

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)


    def creating_cwl_input(self):
        cmd_in = ("script:\n" 
        "  class: File\n"
        "  path: {}\n").format(self.script)
        
        with open("input.yml", "w") as inp_file:
            inp_file.write(cmd_in)


    def run_tests(self):
        for (output, test) in self.tests:
            pass
            # either use pytest.main() https://docs.pytest.org/en/latest/usage.html#calling-pytest-from-python-code
            # or another cwl runner


for workflow in next(os.walk(Workflow_dir))[1]:
    wf = WorkflowRegtest(os.path.join(Workflow_dir, workflow))
    wf.testing_workflow()

                         
    
