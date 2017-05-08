import nibabel as nb
import numpy as np
import os
import pytest, pdb


Data_input_dir = os.path.abspath(__file__ + "/../../data_input")

# TODO: adding git annex
def file2data(filename):
    image = nb.load(filename)
    data = image.get_data()
    return image, data

@pytest.fixture(scope="module")
def image_fmri_nii():
    # for spm it has to be an absolute path
    #pdb.set_trace()
    file_fmri_nii = os.path.join(Data_input_dir, "sub-02_task-fingerfootlips_bold_pr.nii")
    image_fmri_nii, data_fmri_nii = file2data(file_fmri_nii)
    return file_fmri_nii, image_fmri_nii, data_fmri_nii
                

# it might not be needed
@pytest.fixture(scope="module")
def image_fmri():
    file_fmri = os.path.join(Data_input_dir, "sub-02_task-fingerfootlips_bold.nii.gz")
    image_fmri, data_fmri = file2data(file_fmri)
    return file_fmri, image_fmri, data_fmri



def copy_first_image(data_inp):
    data_shape = data_inp.shape[0:3] + (3,)
    new_array = np.zeros(data_shape)

    first_image = data_inp[:,:,:,0]

    for i in range(3):
        new_array[:,:,:,i] = first_image

    return new_array


@pytest.fixture(scope="module")
def image_copy_fmri_nii(image_fmri_nii):
    _, image_fmri, data_fmri = image_fmri_nii

    data_copy = copy_first_image(data_fmri)
    image_copy = nb.Nifti1Image(data_copy, affine=image_fmri.affine)
    filename_copy = os.path.join(Data_input_dir, "sub-02_task-fingerfootlips_bold_pr_copyfirst.nii")
    image_copy.to_filename(filename_copy)
    return filename_copy, data_copy


# it might not be needed
@pytest.fixture(scope="module")
def image_copy_fmri(image_fmri):
    _, image_fmri, data_fmri = image_fmri

    data_copy = copy_first_image(data_fmri)
    image_copy = nb.Nifti1Image(data_copy, affine=image_fmri.affine)
    filename_copy = os.path.join(Data_input_dir, "sub-02_task-fingerfootlips_bold_copyfirst.nii.gz")
    image_copy.to_filename(filename_copy)
    return filename_copy, data_copy



#@pytest.fixture(scope="module")
def image_translate_nii(data_inp, image_inp, n_tr=1, i_orig=1):

    data_shape = data_inp.shape[0:3] + (3,)
    new_array = np.zeros(data_shape)

    first_image = data_inp[:,:,:,0]
    # just to make the task easier   
    first_clean = np.where(first_image>120, first_image, 0)

    new_array[:,:,:,i_orig] = first_clean
    # other images will be translate in one direction                                 
    for i in [j for j in range(3) if j != i_orig]:
        new_array[:-n_tr,:,:,i] = first_clean[n_tr:]
        new_array[:-n_tr,:,:,i] = first_clean[n_tr:]


    new_image = nb.Nifti1Image(new_array, affine=image_inp.affine)
    filename_trans = os.path.join(Data_input_dir, "sub-02_task-fingerfootlips_bold_pr_translation.nii")
    new_image.to_filename(filename_trans)
    return filename_trans, new_array

