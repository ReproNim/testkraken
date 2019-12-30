"""Checking if lists from two json files are equal"""
from __future__ import division
import json
import nibabel as nib
from pathlib import Path


def test_afni_scan_header(file_out, file_ref=None, name=None):

    image_out = nib.load(str(file_out))
    image_ref = nib.load(str(file_ref))

    report_filename = Path(f"report_{name}.json")
    out = {}
    try:
        assert image_out.header == image_ref.header
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

    test_afni_scan_header(**vars(args))
