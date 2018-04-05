import json
import random

def div_list(filename):
    """ a simple function for sorting list"""
    with open(filename) as json_data:
        listorig = json.load(json_data)

    for i in range(len(listorig)):
        listorig[i] /= 2
        listorig[i] += random.random()/100
        
    with open('list_final.json', 'w') as outfile:
        json.dump(listorig, outfile)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a list to sort")
    args = parser.parse_args()

    div_list(args.filename)