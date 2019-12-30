# /usr/bin/env python
from __future__ import division
import json
import os, inspect
from glob import glob
import pandas as pd
import numpy as np
import pdb


def creating_dataframe(files_list):
    """ reads every json file from the files_list and creates one data frame """
    outputmap = {0: "voxels", 1: "volume"}
    df = pd.DataFrame()
    for (i, filename) in enumerate(files_list):
        with open(filename, "rt") as fp:
            in_dict = json.load(fp)
            # in cwl i'm loosing the directory name
            # subject = filename.split(os.path.sep)[-3]
            subject = "subject_{}".format(i)
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
    if type(file_ref) is list:
        expected_files = file_ref
    elif type(file_ref) is str:
        expected_files = [file_ref]

    if type(file_out) is list:
        output_files = file_out
    elif type(file_out) is str:
        output_files = [file_out]

    df_exp = creating_dataframe(expected_files)
    df_out = creating_dataframe(output_files)

    # df_exp.to_csv('output/ExpectedOutput.csv')
    # df_out.to_csv('output/ActualOutput.csv')

    # DJ TOD: this doesn't work, check with the original repo
    # df_diff = df_exp - df_out
    # df_diff = df_diff.dropna()

    report_filename = "report_{}.json".format(name)
    out = {}
    # chosing just a few columns
    keys_test = [
        "white_voxels",
        "gray_voxels",
        "csf_voxels",
        "Right-Hippocampus_voxels",
        "Right-Amygdala_voxels",
        "Right-Caudate_voxels",
    ]
    out["index_name"] = list(df_exp.index)
    for key in keys_test:
        out["re_{}".format(key.replace("_voxels", "").replace("Right-", "R-"))] = []

    for subj in df_exp.index:
        for key in keys_test:
            if df_exp.loc[subj, key] != 0.0:
                out[
                    "re_{}".format(key.replace("_voxels", "").replace("Right-", "R-"))
                ].append(
                    round(
                        1.0
                        * abs(df_exp.loc[subj, key] - df_out.loc[subj, key])
                        / df_exp.loc[subj, key],
                        5,
                    )
                )
            elif df_out.loc[subj, key] != 0.0:
                out[
                    "re_{}".format(key.replace("_voxels", "").replace("Right-", "R-"))
                ].append(1.0)
            else:
                out[
                    "re_{}".format(key.replace("_voxels", "").replace("Right-", "R-"))
                ].append(0.0)

    out["regr"] = []
    for i, subj in enumerate(out["index_name"]):
        list_tmp = []
        for k in out.keys():
            if k not in ["index_name", "regr"]:
                list_tmp.append(out[k][i])
        try:
            assert max(list_tmp) < 0.05
            out["regr"].append("PASSED")
        except (AssertionError):
            out["regr"].append("FAILED")

    # out_max = {"max_diff": max(diff)}
    with open(report_filename, "w") as f:
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
    check_output(**vars(args))
