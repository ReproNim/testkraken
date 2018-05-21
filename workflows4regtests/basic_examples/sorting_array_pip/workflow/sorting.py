import json
import numpy as np

def sorting(filename):
    """ a simple function for sorting list"""
    with open(filename) as json_data:
        list2sort = json.load(json_data)

    array2sort = np.array(list2sort)

    array2sort.sort(axis=0)

    np.save("array_sorted", array2sort)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a list to sort")
    args = parser.parse_args()

    sorting(args.filename)
