import os, pdb


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
        tests_file_l = [i["file"] for i in self.tests]
        self.tests_file_str = ('[' + len(tests_file_l) * '"{}",' + ']').format(*tests_file_l)
        self.report_tests_str = ('[' + len(self.tests_name) * '"report_{}.json",'+ ']').format(
                    *self.tests_name)

    def create_cwl(self):
        self._creating_main_cwl()
        self._creating_main_input() # should be in __init__?
        self._creating_workflow_cwl()
        self._creating_tests_cwl()


    def _creating_workflow_cwl(self):
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
        ).format(self.command, self.image)

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
                "  output_files_tests:\n"
                "    type:\n"
                "      type: array\n"
                "      items: File\n"
                "    outputBinding:\n"
                '      glob: {}\n'
        ).format(self.tests_file_str)

        with open("cwl_workflow.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)



    def _creating_tests_cwl(self):
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
            "      position: 3\n"
            "      prefix: -out\n"
            "  input_ref:\n"
            "    type: File\n"
            "    inputBinding:\n"
            "      position: 4\n"
            "      prefix: -ref\n"
            "  name:\n"
            "    type: string\n"
            "    inputBinding:\n"
            "      position: 5\n"
            "      prefix: -name\n"
            "outputs:\n"
            "  output_files_report:\n"
            "    type: File\n"
            "    outputBinding:\n"
            "      glob: {}\n"
        ).format(self.report_tests_str)

        with open("cwl_tests.cwl", "w") as cwl_file:
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
            "  script_tests:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "  data_ref:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "  name_tests:\n"
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
            "  tests_rep:\n"
            "    type:\n"    
            "      type: array\n"
            "      items: File\n"
            "    outputSource: tests/output_files_report\n"
            "  workflow_out:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "    outputSource: workflow/output_files_tests\n\n"
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
            "    out: [output_files_tests]\n"
            "  tests:\n"
            "    run: cwl_tests.cwl\n"
            "    scatter: [input_files_out, script, input_ref, name]\n"
            "    scatterMethod: dotproduct\n"
            "    in:\n"
            "      script: script_tests\n"
            "      input_files_out: workflow/output_files_tests\n"
            "      input_ref: data_ref\n"
            "      name: name_tests\n"
            "    out: [output_files_report]\n\n"
        )

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)



    def _creating_main_input(self):
        """Creating input yml file for CWL"""

        cmd_in = (
            "script_workf:\n"
            "  class: File\n"
            "  path: {}\n"
            "script_tests:\n"
        ).format(self.script)
        for test in self.tests:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions", test["script"]) + "}\n"
                       )
        cmd_in += "data_ref:\n"
        for test in self.tests:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(self.workflow_path, "data_ref", test["file"]) + "}\n"
                       )
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

        cmd_in += (
            "name_tests: {}\n".format(self.tests_name)
        )

        with open("input.yml", "w") as inp_file:
            inp_file.write(cmd_in)
