import os
import time
from pathlib import Path
import json
import CPAC.utils.test_init as test_utils





def pearson_correlation(file_out, file_ref=None, name=None, **kwargs):
    # out_path = os.path.join(config.workingDirectory, test_wf_name, 'anat_preproc', 'anat_skullstrip',
    #                         input_path[input_path.rindex('/' ) +1:input_path.rindex('.nii.gz') ] +'_resample_brain.nii.gz')


    print("\n \nFILE", file_out, file_ref)
    # TODO should work for a list
    corr = test_utils.pearson_correlation(file_out[0], file_ref[0])
    print(f'\nCorrelation = {round(corr,3)}\n')

    #assert(corr > .99)
    out = {}
    try:
        assert corr > .99
        out["regr"] = "PASSED"
    except (AssertionError):
        out["regr"] = "FAILED"

    report_filename = Path(f"report_{name}.json")

    with report_filename.open("w") as f:
        json.dump(out, f)



if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter

    defstr = " (default %(default)s)"
    parser = ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "-out", nargs="+", dest="file_out", help="file with the output for testing"
    )
    parser.add_argument(
        "-ref", nargs="+", dest="file_ref", help="file with the reference output"
    )
    parser.add_argument(
        "-name", dest="name", help="name of the test provided by a user"
    )
    args = parser.parse_args()
    pearson_correlation(**vars(args))
