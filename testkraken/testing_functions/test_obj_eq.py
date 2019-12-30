"""Checking if lists from two json files are equal"""
from __future__ import division
import json, pandas
from pathlib import Path


def test_obj_eq(file_out, file_ref=None, name=None):

    with open(file_out) as f:
        try:
            obj_out = json.load(f)
            type = "json"
        except:
            try:
                obj_out = pandas.read_csv(file_out)
                type = "csv"
            except:
                type = "txt"
                obj_out = f.read().strip()

    with open(file_ref) as f:
        try:
            obj_ref = json.load(f)
        except:
            try:
                obj_ref = pandas.read_csv(file_ref)
            except:
                obj_ref = f.read().strip()

    report_filename = Path(f"report_{name}.json")
    out = {}
    try:
        if type in ["json", "txt"]:
            assert obj_out == obj_ref
        elif type == "csv":
            assert obj_out.equals(obj_ref)

        out["regr"] = "PASSED"
    except (AssertionError):
        out["regr"] = "FAILED"

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

    test_obj_eq(**vars(args))
