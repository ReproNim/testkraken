"""Checking if two arrays are equal"""

import numpy as np
import json
from pathlib import Path


def test_arr_eq(file_out, file_ref=None, name=None):

    arr_out = np.load(file_out)
    arr_ref = np.load(file_ref)

    out = {}
    try:
        assert (arr_out == arr_ref).all()
        out["regr"] = "PASSED"
    except (AssertionError):
        out["regr"] = "FAILED"

    report_filename = Path(f"report_{name}.json")

    with report_filename.open("w") as f:
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

    test_arr_eq(**vars(args))
