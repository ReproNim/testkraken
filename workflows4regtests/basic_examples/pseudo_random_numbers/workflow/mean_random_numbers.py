import json
import random
import numpy as np

def mean_random_numbers():
    """a function that returns the mean absolute value of the list of pseudo-random numbers"""
    a = random.sample(range(-100, 100), 10)
    mean = np.absolute(a).mean()

    with open('mean.json', 'w') as outfile:
        json.dump(mean, outfile)
