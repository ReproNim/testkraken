"""Checking if lists from two json files are equal"""

import os, json
import inspect

def test_obj_eq(file_out, file_ref, report_txt):
    with open(file_out) as f:
        list_out = json.load(f)
    with open(file_ref) as f:
        list_ref = json.load(f)

    try:
        assert list_out == list_ref
        report_txt.write("Test: {}, OutputFile: {}: PASSED\n".format(inspect.stack()[0][3],
                                                                     file_out))

    except(AssertionError):
        report_txt.write("Test: {}, OutputFile: {}: FAILED\n".format(inspect.stack()[0][3],
                                                                     file_out))

