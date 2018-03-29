import os, pdb


class CwlGenerator(object):
    def __init__(self, image, soft_ver_str, path, parameters):
        self.image = image
        self.soft_ver_str = soft_ver_str
        self.workflow_path = path
        self.script = os.path.join(self.workflow_path, "workflow",
                                   parameters["script"])
        self.command = parameters["command"]
        self.tests_regr = parameters["tests_regr"]
        try:
            self.tests_stat = parameters["tests_stat"]
        except KeyError:
            self.tests_stat = []
        self.inputs = parameters["inputs"]

        #TODO uzywac regr_l i posprzatac
        regr_l = ["{}_{}".format(i[1].split(".")[0], i[0].split(".")[0]) for i in self.tests_regr]
        regr_file_l = [i[0] for i in self.tests_regr]
        self.regr_file_str = ('[' + len(regr_file_l) * '"{}",' + ']').format(*regr_file_l)
        self.report_regr_str = ('[' + len(regr_l) * '"report_{}.json",'+ ']').format(
                    *regr_l)

        stat_l = ["{}_{}".format(i[1].split(".")[0], i[0].split(".")[0]) for i in self.tests_stat]
        stat_file_l = [i[0] for i in self.tests_stat]
        self.stat_file_str = ('[' + len(stat_file_l) * '"{}",' + ']').format(*stat_file_l)
        self.report_stat_str = ('[' + len(stat_l) * '"report_{}.json",' + ']').format(
            *stat_l)

    def create_cwl(self):
        self._creating_main_cwl()
        self._creating_main_input() # should be in __init__?
        self._creating_workflow_cwl()
        self._creating_regr_cwl()
        self._creating_stat_cwl()


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
                "  output_files_regr:\n"
                "    type:\n"
                "      type: array\n"
                "      items: File\n"
                "    outputBinding:\n"
                '      glob: {}\n'
        ).format(self.regr_file_str)
        cmd_cwl += (
                "  output_files_stat:\n"
                "    type:\n"
                "      type: array\n"
                "      items: File\n"
                "    outputBinding:\n"
                '      glob: {}\n'
        ).format(self.stat_file_str)

        with open("cwl_workflow.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)



    def _creating_regr_cwl(self):
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
            "outputs:\n"
            "  output_files_report:\n"
            "    type: File\n"
            "    outputBinding:\n"
            "      glob: {}\n"
        ).format(self.report_regr_str)

        with open("cwl_regr.cwl", "w") as cwl_file:
            cwl_file.write(cmd_cwl)

    def _creating_stat_cwl(self):
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
            "outputs:\n"
            "  output_files_report:\n"
            "    type: File\n"
            "    outputBinding:\n"
            "      glob: {}\n"
        ).format(self.report_stat_str)

        with open("cwl_stat.cwl", "w") as cwl_file:
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
            "  script_regr:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "  data_ref:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "  script_stat:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
        )
        for (ii, input_tuple) in enumerate(self.inputs):
            cmd_cwl += (
            "  input_workf_{}: {}\n"
                ).format(ii, input_tuple[0])
        cmd_cwl += (
            "outputs:\n"
            "  regr_rep:\n"
            "    type:\n"    
            "      type: array\n"
            "      items: File\n"
            "    outputSource: test_regr/output_files_report\n"
            "  stat_rep:\n"
            "    type:\n"
            "      type: array\n"
            "      items: File\n"
            "    outputSource: test_stat/output_files_report\n\n"
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
            "    out: [output_files_regr, output_files_stat]\n"
            "  test_regr:\n"
            "    run: cwl_regr.cwl\n"
            "    scatter: [input_files_out, script, input_ref]\n"
            "    scatterMethod: dotproduct\n"
            "    in:\n"
            "      script: script_regr\n"
            "      input_files_out: workflow/output_files_regr\n"
            "      input_ref: data_ref\n"
            "    out: [output_files_report]\n\n"

            "  test_stat:\n"
            "    run: cwl_stat.cwl\n"
            "    scatter: [input_files_out, script]\n"
            "    scatterMethod: dotproduct\n"
            "    in:\n"
            "      script: script_stat\n"
            "      input_files_out: workflow/output_files_stat\n"
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
            "script_regr:\n"
        ).format(self.script)
        for test in self.tests_regr:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions", test[1]) + "}\n"
                       )
        cmd_in += "data_ref:\n"
        for test in self.tests_regr:
            cmd_in += ("- {class: File, path: " + \
            os.path.join(self.workflow_path, "data_ref", test[0]) + "}\n"
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
        # stat part
        cmd_in += (
            "script_stat:\n"
        ).format(self.script)
        if self.tests_stat:
            for test in self.tests_stat:
                cmd_in += ("- {class: File, path: " + \
                os.path.join(os.path.dirname(os.path.realpath(__file__)), "testing_functions", test[1]) + "}\n"
                           )
        else:
            cmd_in += (" []\n") #TODO should be also for tests_regr

        with open("input.yml", "w") as inp_file:
            inp_file.write(cmd_in)
