"""Defacing Nipype workflow."""

import glob
import os

from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces.io import DataSink
from nipype.interfaces.fsl import BET
from nipype.interfaces.quickshear import Quickshear


# https://github.com/nipy/nipype/blob/704b97dee7848283692bac38f04541c5af2a87b5/nipype/interfaces/quickshear.py#L57-L74
def deface(in_file):
    deface_wf = pe.Workflow('deface_wf')
    inputnode = pe.Node(niu.IdentityInterface(['in_file']),
                     name='inputnode')
    # outputnode = pe.Node(niu.IdentityInterface(['out_file']),
    #                      name='outputnode')
    bet = pe.Node(BET(mask=True), name='bet')
    quickshear = pe.Node(Quickshear(), name='quickshear')
    sinker = pe.Node(DataSink(), name='store_results')
    sinker.inputs.base_directory = os.getcwd()

    deface_wf.connect([
        (inputnode, bet, [('in_file', 'in_file')]),
        (inputnode, quickshear, [('in_file', 'in_file')]),
        (bet, quickshear, [('mask_file', 'mask_file')]),
        (quickshear, sinker, [('out_file', '@')]),
    ])
    inputnode.inputs.in_file = in_file
    res = deface_wf.run()


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument('-i', '--input', dest="in_file",
                        help="Image to deface.")
    args = parser.parse_args()

    deface(args.in_file)
