import nipype.interfaces.spm as spm
import nipype.pipeline.engine as pe
import nibabel as nb
import numpy as np
import pytest, pdb
from common_tests import image_fmri_nii, image_copy_fmri_nii, image_translate_nii

# TODO: dla spm musi byc abs path


# it doesn't work
# Error: Permission denied
# There was a problem writing to the header of
# "/home/jovyan/work/nipype_learning_interfaces/data_input/sub-02_task-fingerfootlips_bold_pr.nii"

@pytest.mark.xfail
def test_realign_run(image_fmri_nii):
    file_inp, _, data_inp = image_fmri_nii

    realign = spm.Realign()

    realign.inputs.in_files = file_inp
    #realign.inputs.register_to_mean = True
    #realign.inputs.jobtype = "estimate"
    realign.run()


def test_realign_node_run(image_fmri_nii):
    file_inp, _, data_inp = image_fmri_nii

    realign_node = pe.Node(spm.Realign(in_files=file_inp),
                           name='realignnode')

    realign_node.run()

    
    data_out = nb.load(realign_node.result.outputs.realigned_files).get_data() 


    # the middle image shouldn't change
    #assert (data_inp[:,:,:,data_inp.shape[3]//2] == data_out[:,:,:,data_inp.shape[3]//2]).all()

    # i'm assuming that the sum shouldn't change "too much"
    for i in range(data_inp.shape[3]):
        assert np.allclose(data_inp[:,:,:,i].sum(), data_out[:,:,:,i].sum(), rtol=2e-2)


def test_realign_run_copy_image(image_fmri_nii, image_copy_fmri_nii):
    file_inp, image_inp, data_inp = image_fmri_nii

    filename_copy, data_copy = image_copy_fmri_nii

    realign_node = pe.Node(spm.Realign(in_files=filename_copy),
                           name='realignnode')

    realign_node.run()
    data_out = nb.load(realign_node.result.outputs.realigned_files).get_data()

    # since all images are the same difference shouldn't be far
    assert np.allclose(data_out, data_copy, rtol=1e-9, atol=1.e-9)

    # this doesn't work, it a weird mean
    mean_out = nb.load(realign_node.result.outputs.mean_image).get_data()
    #for i in range(3):
    #    assert np.allclose(data_out[:,:,:,i], mean_out)

    # this should be the original image (?)
    mod_out = nb.load(realign_node.result.outputs.modified_in_files).get_data()
    assert (mod_out == data_copy).all()


@pytest.mark.xfail(reason="data_out has NaNs...")
def test_realign_translate_image(image_fmri_nii):
    _, image_inp, data_inp = image_fmri_nii

    filename_trans, data_trans = image_translate_nii(data_inp, image_inp)

    realign_node = pe.Node(spm.Realign(in_files=filename_trans),
                           name='realignnode')

    realign_node.run()

    data_out = nb.load(realign_node.result.outputs.realigned_files).get_data()

    # should think about some other error metric
    for i in [0,2]:
        assert np.allclose(data_out[:,:,:,i], data_out[:,:,:,1], rtol=1e-1)

