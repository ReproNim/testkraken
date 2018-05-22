#/usr/bin/env python
from __future__ import division
import json
import os, inspect
from glob import glob
import pandas as pd
import numpy as np
import pdb

def creating_dataframe(files_list):
    """ reads every json file from the files_list and creates one data frame """ 
    outputmap = {0: 'voxels', 1: 'volume'}

    df = pd.DataFrame()
    for filename in files_list:
        with open(filename, 'rt') as fp:
            in_dict = json.load(fp)
            subject = filename.split(os.path.sep)[1]
            in_dict_mod = {}
            for k, v in in_dict.items():
                if isinstance(v, list):
                    for idx, value in enumerate(v):
                        in_dict_mod["%s_%s" % (k, outputmap[idx])] = value
                else:
                    in_dict_mod[k] = v
            df[subject] = pd.Series(in_dict_mod)
    return df.T


def check_output(file_out, file_ref=None, name=None, **kwargs):
    expected_files = [file_ref]
    output_files = [file_out]

    df_exp = creating_dataframe(expected_files)
    df_out = creating_dataframe(output_files)

    #df_exp.to_csv('output/ExpectedOutput.csv')
    #df_out.to_csv('output/ActualOutput.csv')

    # DJ TOD: this doesn't work, check with the original repo
    #df_diff = df_exp - df_out
    #df_diff = df_diff.dropna()

    report_filename = "report_{}.json".format(name)
    out = {}

    for key in df_exp.columns:
        if True:#key in ["white_voxels", "gray_voxels", "csf_voxels", 
                #   "Right-Hippocampus_voxels", "Right-Amygdala_voxels", "Right-Caudate_voxels"]:
            if df_exp[key].values[0] != 0.:
                out["diff:{}".format(key.replace("_voxels", ""))] = round(
                    1. * abs(df_exp[key].values[0] - df_out[key].values[0]) / df_exp[key].values[0], 5)
            elif df_out[key].values[0] != 0.:
                out["diff:{}".format(key.replace("_voxels", ""))] = 1.
            else:
                out["diff:{}".format(key.replace("_voxels", ""))] = 0.

    diff = [val for k, val in out.items()]

    try:
        assert max(diff) < 0.05
        out["regr"] = "PASSED"
    except(AssertionError):
        out["regr"] = "FAILED"

    out_max = {"max_diff": max(diff)}

    with open(report_filename, "w") as f:
        json.dump(out_max, f)


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    defstr = ' (default %(default)s)'
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-out", dest="file_out",
                        help="file with the output for testing")
    parser.add_argument("-ref", dest="file_ref",
                        help="file with the reference output")
    parser.add_argument("-name", dest="name",
                        help="name of the test provided by a user")
    args = parser.parse_args()
    check_output(**vars(args))
