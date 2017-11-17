import nipype.interfaces.spm as spm
import nipype.pipeline.engine as pe
import nibabel as nb
import numpy as np
import os

Data_dir = os.path.abspath(__file__ + "/../..")

def test_realign_regr():
    file_inp = os.path.join(Data_dir, "data_input/sub-02_task-fingerfootlips_bold_pr.nii")
    file_out_ref = os.path.join(Data_dir, "data_ref/sub-02_task-fingerfootlips_bold_SPMrealign.nii")

    realign_node = pe.Node(spm.Realign(in_files=file_inp),
                           name='realignnode')

    realign_node.run()

    data_out = nb.load(realign_node.result.outputs.realigned_files).get_data() 
    data_out_ref = nb.load(file_out_ref).get_data()


    assert np.allclose(data_out_ref, data_out) # think about atol and rtol 



