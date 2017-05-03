from nipype.interfaces.fsl import MCFLIRT
import nibabel as nb
import numpy as np
import pytest, pdb


@pytest.fixture(scope="module")
def image_fmri():
    file_inp = "data_input/sub-02_task-fingerfootlips_bold.nii.gz"
    image_inp = nb.load(file_inp)
    data_inp = image_inp.get_data()
    return file_inp, image_inp, data_inp


@pytest.mark.parametrize("cost_function",
                         ["mutualinfo", "woods", "corratio", "normcorr",
                          "normmi", "leastsquares"])
def test_mcflirt_run(image_fmri, cost_function):
    file_inp, _, data_inp = image_fmri

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


def test_mcflirt_run_copy_image(image_fmri):
    _, image_inp, data_inp = image_fmri

    mcflt = MCFLIRT()

    new_array = np.zeros((64, 64, 30, 3))
    first_image = data_inp[:,:,:,0]
    for i in range(3):
        new_array[:,:,:,i] = first_image

    new_image = nb.Nifti1Image(new_array, affine=image_inp.affine)
    new_image.to_filename("new_file.nii.gz")


    mcflt.inputs.in_file = "new_file.nii.gz"
    mcflt.inputs.out_file = "output_mcf_copy.nii.gz"
    mcflt.basedir = "test"
    pdb.set_trace()

    mcflt.run()

    img_out = nb.load(mcflt.inputs.out_file)
    data_out = img_out.get_data()

    # since all images are the same mcflirt shouldn't do anything
    assert (new_array == data_out).all()


@pytest.mark.xfail(reason="have to find better error mtric")
def test_mcflirt_translate_image(image_fmri):
    _, image_inp, data_inp = image_fmri

    mcflt = MCFLIRT()


    new_array = np.zeros((64, 64, 30, 3))
    first_image = data_inp[:,:,:,0]
    # just to make the task easier
    first_clean = np.where(first_image>120, first_image, 0)


    new_array[:,:,:,1] = first_clean
    # the first and third image will be translate in one direction
    new_array[:63,:,:,0] = first_clean[1:]
    new_array[:63,:,:,2] = first_clean[1:]


    new_image = nb.Nifti1Image(new_array, affine=image_inp.affine)
    new_image.to_filename("new_translation_file.nii.gz")


    mcflt.inputs.in_file = "new_translation_file.nii.gz"
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
