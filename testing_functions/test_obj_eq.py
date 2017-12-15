"""Checking if lists from two json files are equal"""

import os, json
import inspect

def test_obj_eq(file_out, file_ref, report_filename):

    with open(file_out) as f:
        try:
            obj_out = json.load(f)
        except:
            obj_out = f.read().strip()

    with open(file_ref) as f:
        try:
            obj_ref = json.load(f)
        except:
            obj_ref = f.read().strip()

    try:
        assert obj_out == obj_ref
        with open(report_filename, "a") as f:
            f.write("Test: {}, OutputFile: {}: PASSED\n".format(inspect.stack()[0][3],
                                                                os.path.basename(file_out)))

    except(AssertionError):
        with open(report_filename, "a") as f:
            f.write("Test: {}, OutputFile: {}: FAILED\n".format(inspect.stack()[0][3],
                                                                os.path.basename(file_out)))


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-out", dest="file_out",
                        help="file with the output for testing")
    parser.add_argument("-ref", dest="file_ref",
                        help="file with the reference output")
    parser.add_argument("-report", dest="report_filename",
                        help="file to save tests output")
    args = parser.parse_args()

    test_obj_eq(**vars(args))
