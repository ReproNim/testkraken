from nipype.interfaces.fsl import MCFLIRT
import nibabel as nb
import numpy as np
import pdb

def test_mcflirt_run():
    file_inp = "data_input/ds000114_sub-01_T1w.nii.gz"
    file_out_ref = "data_ref/ds000114_sub-01_T1w_mcf.nii.gz"


    mcflt = MCFLIRT()

    mcflt.inputs.in_file = file_inp
    mcflt.inputs.out_file = "output_mcf.nii.gz"

    mcflt.run()

    data_out_ref = nb.load(file_out_ref).get_data()
    data_out = nb.load(mcflt.inputs.out_file).get_data()

    assert np.allclose(data_out_ref, data_out) # think about atol and rtol

