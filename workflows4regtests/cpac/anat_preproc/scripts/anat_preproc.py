import os
from CPAC.pipeline.cpac_pipeline import initialize_nipype_wf, \
    load_cpac_pipe_config, connect_pipeline, build_anat_preproc_stack
from CPAC.pipeline.engine import initiate_rpool
from CPAC.utils.bids_utils import create_cpac_data_config


def test_build_anat_preproc_stack(pipe_config, bids_dir, test_dir):
    
    sub_data_dct = create_cpac_data_config(bids_dir,
                                           skip_bids_validator=True)[0]
    cfg = load_cpac_pipe_config(pipe_config)

    cfg.pipeline_setup['output_directory']['path'] = \
        os.path.join(test_dir, 'out')
    cfg.pipeline_setup['working_directory']['path'] = \
        os.path.join(test_dir, 'work')
    cfg.pipeline_setup['log_directory']['path'] = \
        os.path.join(test_dir, 'logs')

    wf = initialize_nipype_wf(cfg, sub_data_dct)

    wf, rpool = initiate_rpool(wf, cfg, sub_data_dct)

    pipeline_blocks = build_anat_preproc_stack(rpool, cfg)
    wf = connect_pipeline(wf, cfg, rpool, pipeline_blocks)

    rpool.gather_pipes(wf, cfg)

    wf.run()

if __name__ == '__main__':

    from argparse import ArgumentParser, RawTextHelpFormatter

    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)

    parser.add_argument("-i", dest="input_path",
                        help="input file path")

    parser.add_argument("-w", dest="working_path",
                        help="working_path")

    args = parser.parse_args()
    cfg = "pipeline_config_anat_preproc.yml"

    test_build_anat_preproc_stack(pipe_config=cfg, bids_dir=args.input_path, test_dir=args.working_path)