"""testing the results for a specific seed"""

import os, json
import inspect
import random
#import numpy as np


def stat_list(file_out):
    with open(file_out) as f:
        res_out = json.load(f)
    
    out = {}
    out["sum"] = sum(res_out)
    
    report_filename = "report_{}_{}".format(inspect.stack()[0][3], os.path.basename(file_out))
    with open(report_filename, "a") as f:
        json.dump(out, f)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-out", dest="file_out",
                        help="file with the output for testing")
    args = parser.parse_args()

    stat_list(**vars(args))

