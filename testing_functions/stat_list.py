"""testing the results for a specific seed"""

import os, json
import inspect
import random
#import numpy as np


def list_stat(file_out, report_filename):
    with open(file_out) as f:
        res_out = json.load(f)
    
    out = {}
    out["sum"] = sum(res_out)
    

    with open(report_filename, "a") as f:
        json.dump(out, f)

#w test_main powinnam sprawdzac, czy jest ref, albo miec argument do test main w zaleznosci czy one sa stat, czy nie, moze ejdnak osobny step?
if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-out", dest="file_out",
                        help="file with the output for testing")
    parser.add_argument("-report", dest="report_filename",
                        help="file to save tests output")
    args = parser.parse_args()

    list_stat(**vars(args))

