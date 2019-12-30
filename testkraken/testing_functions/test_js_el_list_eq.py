"""Checking if lists from two json files are equal"""
from __future__ import division
import os, json, pdb
import inspect


def test_el_list_eq(file_out, file_ref=None, name=None, **kwargs):
    """ comparing elements of the lists saved in two json files: file_out, file_ref"""

    # loading data of our workflow
    with open(file_out) as f:
        obj_out = json.load(f)
    # loadin the reference results
    with open(file_ref) as f:
        obj_ref = json.load(f)

    # creating name for the report file
    report_filename = "report_{}.json".format(name)

    out = {}
    out["rel_error"] = []
    out["abs_error"] = []
    out["index_name"] = []

    # calculating errors for every element of the list
    for i, el in enumerate(obj_ref):
        out["index_name"].append("el_{}".format(i))
        out["abs_error"].append(abs(obj_ref[i] - obj_out[i]))
        out["rel_error"].append(abs(obj_ref[i] - obj_out[i]) / obj_ref[i])

    # saving the output
    with open(report_filename, "w") as f:
        json.dump(out, f)


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter

    parser = ArgumentParser(description=__doc__, formatter_class=RawTextHelpFormatter)
    parser.add_argument(
        "-out", dest="file_out", help="file with the output for testing"
    )
    parser.add_argument("-ref", dest="file_ref", help="file with the reference output")
    parser.add_argument(
        "-name", dest="name", help="name of the test provided by a user"
    )
    args = parser.parse_args()

    test_el_list_eq(**vars(args))
