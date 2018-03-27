import os


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

        test_name_l = [i[1] for i in self.tests]
        self.test_name_str = ('[' + len(test_name_l) * '"{}",' + ']').format(*test_name_l)
        test_file_l = [i[0] for i in self.tests]
        self.test_file_str = ('[' + len(test_file_l) * '"{}",' + ']').format(*test_file_l)
        self.report_str = ('[' + len(test_name_l) * '"report_{}_{}_{}.txt",'.format(
            {}, os.path.basename(self.workflow_path), self.soft_ver_str) + ']').format(
                    *range(len(self.tests)))



    def create_cwl(self):
        self._creating_main_cwl()
        self._creating_main_input() # should be in __init__?
        self._creating_workflow_cwl()
        self._creating_test_cwl()


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
                "  output_files:\n"
                "    type:\n"
                "      type: array\n"
                "      items: File\n"
                "    outputBinding:\n"
                '      glob: {}\n'
        ).format(self.test_file_str)

        with open("cwl_workflow.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)



    def _creating_test_cwl(self):
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
            "  input_files_report:\n"
            "    type: string\n"
            "    inputBinding:\n"
            "      position: 5\n"
            "      prefix: -report\n"
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
            "  script_test:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "  data_ref:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
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
            "    scatter: [input_files_out, script, input_ref, input_files_report]\n"
            "    scatterMethod: dotproduct\n"
            "    in:\n"
            "      script: script_test\n"
            "      input_files_out: workflow/output_files\n"
            "      input_ref: data_ref\n"
            "      input_files_report: report_txt\n"
            "    out: [output_files_report]"
                )

        with open("cwl.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)



    def _creating_main_input(self):
        """Creating input yml file for CWL"""

        cmd_in = (
            "script_workf:\n"
            "  class: File\n"
            "  path: {}\n"
            "script_test:\n"
        ).format(self.script)
        for test in self.tests:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions", test[1]) + "}\n"
                       )
        cmd_in += "data_ref:\n"
        for test in self.tests:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(self.workflow_path, "data_ref", test[0]) + "}\n"
                       )
        cmd_in += ("report_txt: {}\n").format(self.report_str)
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
