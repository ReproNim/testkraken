"""testing the results for a specific seed"""

import os, json
import inspect
import random
#import numpy as np

def test_rand_almosteq(file_out, file_ref, report_txt):
    with open(file_out) as f:
        res_out = json.load(f)
    with open(file_ref) as f:
        res_ref = json.load(f)

    try:
        #np.testing.assert_almost_equal(res_out, res_ref)
        assert abs(res_out - res_ref) < 0.1

        report_txt.write("Test: {}, OutputFile: {}: PASSED\n".format(inspect.stack()[0][3],
                                                                     file_out))

    except(AssertionError):
        report_txt.write("Test: {}, OutputFile: {}: FAILED\n".format(inspect.stack()[0][3],
                                                                     file_out))

