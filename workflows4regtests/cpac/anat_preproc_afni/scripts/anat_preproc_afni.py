import os
import nipype.pipeline.engine as pe
import nipype.interfaces.utility as util
from CPAC.utils import Configuration, Strategy
from CPAC.anat_preproc.anat_preproc import create_anat_preproc


def file_node(path, file_node_num=0):
    '''
    Create an identity node given a file path
    Parameters
    ----------
    path : string
        file path
    file_node_num : int
        number of file node

    Returns
    -------
    input_node : identity node
        an identity node of the input file path
    '''

    input_node = pe.Node(
        util.IdentityInterface(fields=['file']), name='file_node_{0}'.format(file_node_num)
    )
    input_node.inputs.file = path

    return input_node, 'file'


def anat_preproc_afni(working_path, input_path, test_wf_name='test_anat_preproc_afni'):
    '''
    Test create_anat_preproc() with AFNI
    Parameters
    ----------
    working_path : string
        nipype working directory
    input_path : string
        input file path
    test_wf_name : string
        name of test workflow

    Returns
    -------
    None
    '''

    # create a configuration object
    config = Configuration({
        "num_ants_threads": 4,
        "workingDirectory": os.path.join(working_path, "working"),
        "crashLogDirectory": os.path.join(working_path, "crash"),
        "outputDirectory": working_path,
        "non_local_means_filtering": False,
        "n4_bias_field_correction": False,
        "skullstrip_mask_vol": False,
        "skullstrip_shrink_factor": 0.6,
        "skullstrip_var_shrink_fac": True,
        "skullstrip_shrink_factor_bot_lim": 0.4,
        "skullstrip_avoid_vent": True,
        "skullstrip_n_iterations": 250,
        "skullstrip_pushout": True,
        "skullstrip_touchup": True,
        "skullstrip_fill_hole": 10,
        "skullstrip_NN_smooth": 72,
        "skullstrip_smooth_final": 20,
        "skullstrip_avoid_eyes": True,
        "skullstrip_use_edge": True,
        "skullstrip_exp_frac": 0.1,
        "skullstrip_push_to_edge": False,
        "skullstrip_use_skull": False,
        "skullstrip_perc_int": 0,
        "skullstrip_max_inter_iter": 4,
        "skullstrip_fac": 1,
        "skullstrip_blur_fwhm": 0,
        "skullstrip_monkey": False,
    })

    # mock the strategy
    strat = Strategy()

    resource_dict = {
        "anatomical": input_path
    }

    file_node_num = 0
    for resource, filepath in resource_dict.items():
        strat.update_resource_pool({
            resource: file_node(filepath, file_node_num)
        })
        strat.append_name(resource + '_0')
        file_node_num += 1

    # build the workflow
    workflow = pe.Workflow(name=test_wf_name)
    workflow.base_dir = config.workingDirectory
    workflow.config['execution'] = {
        'hash_method': 'timestamp',
        'crashdump_dir': os.path.abspath(config.crashLogDirectory)
    }

    # call create_anat_preproc
    anat_preproc = create_anat_preproc(method='afni',
                                       already_skullstripped=False,
                                       config=config,
                                       wf_name='anat_preproc',
                                       sub_dir=None #TODO
                                       )

    # connect AFNI options
    anat_preproc.inputs.AFNI_options.set(
        mask_vol=config.skullstrip_mask_vol,
        shrink_factor=config.skullstrip_shrink_factor,
        var_shrink_fac=config.skullstrip_var_shrink_fac,
        shrink_fac_bot_lim=config.skullstrip_shrink_factor_bot_lim,
        avoid_vent=config.skullstrip_avoid_vent,
        niter=config.skullstrip_n_iterations,
        pushout=config.skullstrip_pushout,
        touchup=config.skullstrip_touchup,
        fill_hole=config.skullstrip_fill_hole,
        avoid_eyes=config.skullstrip_avoid_eyes,
        use_edge=config.skullstrip_use_edge,
        exp_frac=config.skullstrip_exp_frac,
        smooth_final=config.skullstrip_smooth_final,
        push_to_edge=config.skullstrip_push_to_edge,
        use_skull=config.skullstrip_use_skull,
        perc_int=config.skullstrip_perc_int,
        max_inter_iter=config.skullstrip_max_inter_iter,
        blur_fwhm=config.skullstrip_blur_fwhm,
        fac=config.skullstrip_fac,
        monkey=config.skullstrip_monkey
    )

    node, out_file = strat['anatomical']
    workflow.connect(node, out_file,
                     anat_preproc, 'inputspec.anat')

    # run workflow
    workflow.run()


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-i", dest="input_path",
                        help="input file path")

    parser.add_argument("-w", dest="working_path",
                        help="working_path")


    args = parser.parse_args()

    anat_preproc_afni(input_path=args.input_path, working_path=args.working_path)
