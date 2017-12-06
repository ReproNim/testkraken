import json

def sorting(filename):

    with open(filename) as json_data:
        list2sort = json.load(json_data)

    list2sort.sort()

    with open('list_sorted.json', 'w') as outfile:
        json.dump(list2sort, outfile)
        
    print("sorted list: {}".format(list2sort))


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a list to sort")
    args = parser.parse_args()

    sorting(args.filename)
