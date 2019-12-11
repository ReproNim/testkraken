# This file provides a user-facing command-line interface (CLI) to your workflow

# A template workflow is provided in workflow.py
# If you change the name there, change the name here, as well.
import sys
from .workflow import init_unifize_and_skullstrip_wf

# The main function is what will be run when niflow-coco2019-unifize_and_skullstrip is called
# Command-line arguments are available via the sys.argv list, though you may find it easier
# to construct non-trivial command lines using either of the following libraries:
#  * argparse (https://docs.python.org/3/library/argparse.html)
#  * click (https://click.palletsprojects.com)
def main():
    wf = init_unifize_and_skullstrip_wf()
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    wf.inputs.inputnode.in_file = in_file
    wf.inputs.inputnode.out_file = out_file
    wf.run()
