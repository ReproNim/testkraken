import json

def sorting(filename):

    with open(filename) as json_data:
        list2sort = json.load(json_data)

    list2sort.sort()

    with open('list_sorted.json', 'w') as outfile:
        json.dump(list2sort, outfile)

sorting('../data_input/list2sort.json')

