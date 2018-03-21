import subprocess
import os
import pdb

def edit_main(test_name, dir, file_out, dir_ref, file_report): 
    file_test = os.path.join(dir, test_name)
    file_ref = os.path.join(dir_ref, os.path.split(file_out)[1])
    os.path.isfile(file_test)
    subprocess.call(["python", file_test, "-out", file_out, "-ref", file_ref, "-report", file_report])


if __name__ == "__main__":
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-test", dest="test_name")
    parser.add_argument("-dir", dest="dir")
    parser.add_argument("-out", dest="file_out")
    parser.add_argument("-ref", dest="dir_ref")
    parser.add_argument("-report", dest="file_report")
    args = parser.parse_args()
    edit_main(**vars(args))
