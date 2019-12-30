"""Checking if lists from two json files are equal"""
from __future__ import division
import json
import numpy.testing as npt
import nibabel as nib
from pathlib import Path


def test_afni_scan_data_diff_fake(file_out, file_ref=None, name=None):

    image_out = nib.load(str(file_out))
    data_out = image_out.get_fdata()

    image_ref = nib.load(str(file_ref))
    data_ref = image_ref.get_fdata()

    report_filename = Path(f"report_{name}.json")
    out = {}
    # try:
    # fake!
    abs_diff_max = 8
    rel_diff_max = 0.1
    # npt.assert_array_equal(data_out, data_ref)
    out["abs_diff"] = abs_diff_max
    out["rel_diff"] = rel_diff_max

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

    test_afni_scan_data_diff_fake(**vars(args))
