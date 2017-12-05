import json

def sorting(filename):

    with open(filename) as json_data:
        list2sort = json.load(json_data)

    list2sort.sort()

    with open('list_sorted.json', 'w') as outfile:
        json.dump(list2sort, outfile)
        
    print("sorted list: {}".format(list2sort))

sorting('/data_input/list2sort.json')
#for testing
#with open('tmp_list.json', 'w') as outfile:
#    json.dump([10, 3, 9], outfile)
#sorting("tmp_list.json")
