"""Comparing statistics after AFNI run (out.ss_review.FT.txt file)"""
from __future__ import division
import os, json, pdb


def creating_dictionary(filename):
    res_dict = {}
    with open(filename) as f:
        for line in f:
            key_val = [k.strip() for k in line.split(":")]
            if len(key_val) == 2:
                try:
                    val = [float(v) for v in key_val[1].split()]
                except ValueError:
                    continue
                res_dict[key_val[0]] = val
    return res_dict

def test_file_eq(file_out, file_ref=None, name=None, **kwargs):
    out = {}
    dict_out = creating_dictionary(file_out)
    dict_ref = creating_dictionary(file_ref)

    for key, val_r in  dict_ref.items():
        print("ALL KEYS: ", key, dict_ref[key], dict_out[key])
        if (key not in dict_out.keys()) or (len(dict_out[key]) != len(dict_ref[key])):
            error = -99999
        else:
            er_l = []
            for ii in range(len(dict_ref[key])):
                if dict_ref[key][ii] != 0:
                    er_l.append(round(1. * abs(dict_ref[key][ii] - dict_out[key][ii]) / dict_ref[key][ii], 5))
                elif dict_ref[key][ii] == 0 and dict_out[key][ii] != 0:
                    er_l.append(1)
                else:
                    er_l.append(0)
            error = max(er_l)
        if ("blur" in key or "ave" in key) and ("FWHM" not in key) and ("sresp" not in key):
            out["max_rel_error: {}".format(key)] = error

    report_filename = "report_{}.json".format(name)
    print("TEST", report_filename)


    with open(report_filename, "w") as f:
        json.dump(out, f)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-out", dest="file_out",
                        help="file with the output for testing")
    parser.add_argument("-ref", dest="file_ref",
                        help="file with the reference output")
    parser.add_argument("-name", dest="name",
                        help="name of the test provided by a user")
    args = parser.parse_args()

    test_file_eq(**vars(args))
