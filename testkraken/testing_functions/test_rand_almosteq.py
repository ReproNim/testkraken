"""testing the results for a specific seed"""
from __future__ import division
import os, json
import inspect
import random

# import numpy as np


def test_rand_almosteq(file_out, file_ref=None, name=None, **kwargs):
    with open(file_out) as f:
        res_out = json.load(f)
    with open(file_ref) as f:
        res_ref = json.load(f)

    report_filename = "report_{}.json".format(name)
    print("TEST", report_filename)
    out = {}
    diff = abs(res_out - res_ref) / res_ref
    out["diff"] = diff
    try:
        assert diff < 0.05
        out["regr"] = "PASSED"
    except (AssertionError):
        out["regr"] = "FAILED"

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

    test_rand_almosteq(**vars(args))
