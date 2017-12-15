import json

def sorting(filename):
    """ a simple function for sorting list"""
    with open(filename) as json_data:
        list2sort = json.load(json_data)

    list2sort.sort()

    with open('list_sorted.json', 'w') as outfile:
        json.dump(list2sort, outfile)
    with open('sum_list.json', 'w') as outfile:
        json.dump(sum(list2sort), outfile)
        
    print("sorted list: {}".format(list2sort))


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a list to sort")
    args = parser.parse_args()

    sorting(args.filename)
