from nipype.interfaces.fsl import MCFLIRT
import nibabel as nb

def test_mcflirt_run():
    file_inp = "data_input/sub-02_task-fingerfootlips_bold.nii.gz"

    mcflt = MCFLIRT()

    mcflt.inputs.in_file = file_inp
    mcflt.inputs.out_file = "output_mcf.nii.gz"
    mcflt.basedir = "test"

    mcflt.run()

    data_in = nb.load(file_inp).get_data()
    data_out = nb.load(mcflt.inputs.out_file).get_data()

    assert (data_in[:,:,:,data_in.shape[3]//2] == data_out[:,:,:,data_in.shape[3]//2]).all()

    for i in range(data_in.shape[3]):
        assert data_in[:,:,:,i].sum() - data_out[:,:,:,i].sum() <= 0.005 * data_in[:,:,:,i].sum()
        #print(data_in[:,:,:,i].sum() - data_out[:,:,:,i].sum())
        #print(data_in[:,:,:,i].sum())

    #assert data_in.sum() == data_out.sum()
    #assert data_in.max() == data_out.max() # can I compare max?
