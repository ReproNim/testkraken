"""testing the results for a specific seed"""
from __future__ import division
import os, json
import inspect
import random
#import numpy as np


def stat_list(file_out, file_ref=None, name=None, **kwargs):
    with open(file_out) as f:
        res_out = json.load(f)

    report_filename = "report_{}.json".format(name)
    print("STAT", report_filename)
    out = {}
    out["sum"] = sum(res_out)
    
    with open(report_filename, "a") as f:
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

    stat_list(**vars(args))

