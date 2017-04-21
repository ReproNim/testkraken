from nipype.interfaces.fsl import MCFLIRT
import nibabel as nb
import numpy as np
import pytest

def test_mcflirt_run():
    file_inp = "data_input/sub-02_task-fingerfootlips_bold.nii.gz"

    mcflt = MCFLIRT()

    mcflt.inputs.in_file = file_inp
    mcflt.inputs.out_file = "output_mcf.nii.gz"
    mcflt.basedir = "test"

    mcflt.run()

    data_in = nb.load(file_inp).get_data()
    data_out = nb.load(mcflt.inputs.out_file).get_data()

    # the middle image shouldn't change
    assert (data_in[:,:,:,data_in.shape[3]//2] == data_out[:,:,:,data_in.shape[3]//2]).all()

    # i'm assuming that the sum shouldn't change "too much"
    for i in range(data_in.shape[3]):
        assert np.allclose(data_in[:,:,:,i].sum(), data_out[:,:,:,i].sum(), rtol=5e-3)


def test_mcflirt_run_copy_image():
    file_orig = "data_input/sub-02_task-fingerfootlips_bold.nii.gz"

    image_orig = nb.load(file_orig)

    mcflt = MCFLIRT()

    new_array = np.zeros((64, 64, 30, 3))
    first_image = image_orig.get_data()[:,:,:,0]
    for i in range(3):
        new_array[:,:,:,i] = first_image

    new_image = nb.Nifti1Image(new_array, affine=image_orig.affine)
    new_image.to_filename("new_file.nii.gz")


    mcflt.inputs.in_file = "new_file.nii.gz"
    mcflt.inputs.out_file = "output_mcf_copy.nii.gz"
    mcflt.basedir = "test"

    mcflt.run()

    img_out = nb.load(mcflt.inputs.out_file)
    data_out = img_out.get_data()

    # since all images are the same mcflirt shouldn't do anything
    assert (new_array == data_out).all()


def test_mcflirt_translate_image():
    file_orig = "data_input/sub-02_task-fingerfootlips_bold.nii.gz"

    image_orig = nb.load(file_orig)

    mcflt = MCFLIRT()

    new_array = np.zeros((64, 64, 30, 3))
    first_image = image_orig.get_data()[:,:,:,0]
    # just to make the task easier
    first_clean = np.where(first_image>120, first_image, 0)


    new_array[:,:,:,1] = first_clean
    # the first and third image will be translate in one direction
    new_array[:59,:,:,0] = first_clean[5:]
    new_array[:59,:,:,2] = first_clean[5:]


    new_image = nb.Nifti1Image(new_array, affine=image_orig.affine)
    new_image.to_filename("new_translation_file.nii.gz")


    mcflt.inputs.in_file = "new_translation_file.nii.gz"
    mcflt.inputs.out_file = "output_mcf_trans.nii.gz"
    mcflt.basedir = "test"

    mcflt.run()

    img_out = nb.load(mcflt.inputs.out_file)
    data_out = img_out.get_data()

    # should think about some other error metric
    # this one gives a big error
    for i in [0,2]:
        assert np.allclose(data_out[:,:,:,i], data_out[:,:,:,1], rtol=1e-1)
