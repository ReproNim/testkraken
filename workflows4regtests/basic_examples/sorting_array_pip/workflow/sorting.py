import json, os
import numpy as np

def sorting(filename, outputdir):
    """ a simple function for sorting list"""
    with open(filename) as json_data:
        list2sort = json.load(json_data)

    array2sort = np.array(list2sort)

    array2sort.sort(axis=0)

    file_sort = os.path.join(outputdir, 'array_sorted')

    np.save(file_sort, array2sort)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a list to sort")
    parser.add_argument("-o", dest="outputdir",
                        help="directory with the output")
    args = parser.parse_args()

    sorting(args.filename, args.outputdir)
