from nipype.interfaces.fsl import MCFLIRT
import nibabel as nb
import numpy as np
import pytest, pdb
from common_tests import image_fmri_nii, image_copy_fmri_nii, image_translate_nii


@pytest.mark.parametrize("cost_function",
                         ["mutualinfo", "woods", "corratio", "normcorr",
                          "normmi", "leastsquares"])
def test_mcflirt_run(image_fmri_nii, cost_function):
    file_inp, _, data_inp = image_fmri_nii

    mcflt = MCFLIRT()

    mcflt.inputs.in_file = file_inp
    mcflt.inputs.out_file = "output_mcf.nii.gz"
    mcflt.basedir = "test"
    setattr(mcflt.inputs, "cost", cost_function)

    mcflt.run()

    data_out = nb.load(mcflt.inputs.out_file).get_data()

    # the middle image shouldn't change
    assert (data_inp[:,:,:,data_inp.shape[3]//2] == data_out[:,:,:,data_inp.shape[3]//2]).all()

    # i'm assuming that the sum shouldn't change "too much"
    for i in range(data_inp.shape[3]):
        assert np.allclose(data_inp[:,:,:,i].sum(), data_out[:,:,:,i].sum(), rtol=5e-3)


def test_mcflirt_run_copy_image(image_fmri_nii, image_copy_fmri_nii):
    _, image_inp, data_inp = image_fmri_nii
    filename_copy, data_copy = image_copy_fmri_nii

    mcflt = MCFLIRT()

    mcflt.inputs.in_file = filename_copy
    mcflt.inputs.out_file = "output_mcf_copy.nii.gz"
    mcflt.basedir = "test"

    mcflt.run()

    img_out = nb.load(mcflt.inputs.out_file)
    data_out = img_out.get_data()

    # since all images are the same mcflirt shouldn't do anything
    assert (data_copy == data_out).all()


@pytest.mark.xfail(reason="the error is too big")
def test_mcflirt_translate_image(image_fmri_nii):
    _, image_inp, data_inp = image_fmri_nii

    mcflt = MCFLIRT()

    filename_trans, data_trans = image_translate_nii(data_inp, image_inp)

    mcflt.inputs.in_file = filename_trans
    mcflt.inputs.out_file = "output_mcf_trans.nii.gz"
    mcflt.basedir = "test"
    mcflt.inputs.smooth = 0.
    
    mcflt.run()

    img_out = nb.load(mcflt.inputs.out_file)
    data_out = img_out.get_data()

    # should think about some other error metric
    # this one gives a big error
    # mcflt.inputs.smooth = 0. doesn't really change
    for i in [0,2]:
        assert np.allclose(data_out[:,:,:,i], data_out[:,:,:,1], rtol=1e-1)
