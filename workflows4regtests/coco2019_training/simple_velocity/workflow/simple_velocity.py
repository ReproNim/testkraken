import json

def velocity(filename):
    # loading data from a json file
    with open(filename) as json_data:
        data = json.load(json_data)

    # the initial position
    x_i = data["x_init"]
    # the final position
    x_f = data["x_final"]
    # time
    time = data["time"]

    #list for velocity results
    velocity = []

    # iterating over all elements
    for i in range(len(time)):
        # calculate velocity: v = \Delta x / time = (x_f - x_i) / time
        v = (x_f[i] - x_i[i]) / time[i]
        # saving value of the velocity rounded to the intigare
        velocity.append(round(v))

    # saving the list with the results
    with open('velocity.json', 'w') as outfile:
        json.dump(velocity, outfile)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-f", dest="filename",
                        help="file with a data: dictionary with x_init, x_final, time")
    args = parser.parse_args()

    velocity(args.filename)


