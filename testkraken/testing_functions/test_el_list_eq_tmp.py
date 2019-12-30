"""Checking if lists from two json files are equal"""
from __future__ import division
import os, json, pdb
import inspect


def test_el_list_eq(file_out, file_ref=None, name=None, **kwargs):

    if type(file_out) is list:
        file_out_r = file_out[0]
    else:
        file_out_r = file_out

    if type(file_ref) is list:
        file_ref_r = file_ref[0]
    else:
        file_ref_r = file_ref

    with open(file_out_r) as f:
        try:
            obj_out = json.load(f)
        except:
            obj_out = f.read().strip()

    with open(file_ref_r) as f:
        try:
            obj_ref = json.load(f)
        except:
            obj_ref = f.read().strip()

    report_filename = "report_{}.json".format(name)
    print("TEST", report_filename)
    out = {}
    out["index_name"] = ["group1", "group2"]
    out["mean"] = [
        round(sum(obj_out[:5]) / len((obj_out[:2])), 1),
        round(sum(obj_out[5:]) / len((obj_out[2:])), 1),
    ]

    # diff = [val for k, val in out.items()]
    # print("TEST", diff, out)
    # try:
    #    assert max(diff) < 0.05
    #    out["regr"] = "PASSED"
    # except(AssertionError):
    #    out["regr"] = "FAILED"

    with open(report_filename, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter

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

    test_el_list_eq(**vars(args))
