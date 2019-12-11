# This file demonstrates a workflow-generating function, a particular convention for generating
# nipype workflows. Others are possible.

# Every workflow need pe.Workflow [0] and pe.Node [1], and most will need basic utility
# interfaces [2].
# [0] https://nipype.rtfd.io/en/latest/api/generated/nipype.pipeline.engine.workflows.html
# [1] https://nipype.rtfd.io/en/latest/api/generated/nipype.pipeline.engine.nodes.html
# [2] https://nipype.rtfd.io/en/latest/interfaces/generated/nipype.interfaces.utility/base.html
from nipype.pipeline import engine as pe
from nipype.interfaces import fsl
from nipype.interfaces import afni
from nipype.interfaces import utility as niu

def init_unifize_and_skullstrip_wf(name='unifize_and_skullstrip_wf'):
    wf = pe.Workflow(name=name)

    # inputnode/outputnode can be thought of as the parameters and return values of a function
    inputnode = pe.Node(niu.IdentityInterface(['in_file', 'out_file']), name='inputnode')
    outputnode = pe.Node(niu.IdentityInterface(['out_file']), name='outputnode')

    #
    # The rest of the workflow should be defined here.
    #
    bet = pe.Node(fsl.BET(), name='bet')
    unifize = pe.Node(afni.Unifize(outputtype='NIFTI'), name='unifize')

    wf.connect([
        (inputnode, bet, [('in_file', 'in_file')]),
        (bet, unifize, [('out_file', 'in_file')]),
        (inputnode, unifize, [('out_file', 'out_file')]),
        (unifize, outputnode, [('out_file', 'out_file')]),
        ])

    return wf
