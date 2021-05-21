import json
import random

def mean_random_numbers(k):
    """a function that returns the mean absolute value of the list of pseudo-random numbers"""
    random.seed(k)
    a = random.sample(range(-100, 100), 10)
    a_abs = [abs(int(i)) for i in a]

    mean = sum(a_abs) / len(a_abs)

    with open('mean.json', 'w') as outfile:
        json.dump(mean, outfile)

    with open('mean_2.json', 'w') as outfile:
        json.dump(mean*2, outfile)


if __name__ == '__main__':
    mean_random_numbers(2)
