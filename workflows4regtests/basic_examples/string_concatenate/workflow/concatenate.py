
def concatenate(string_list, n=1):
    """ a simple function to concatenate strings"""

    final_str = "".join(string_list) * n

    with open('string_conc.txt', 'w') as outfile:
        outfile.write(final_str)


if __name__ == '__main__':
    from argparse import ArgumentParser, RawTextHelpFormatter
    parser = ArgumentParser(description=__doc__,
                            formatter_class=RawTextHelpFormatter)
    parser.add_argument("-s", dest="string_list",
                        help="list of strings")
    parser.add_argument("-n", dest="n", type=int,
                        help="factor")

    args = parser.parse_args()

    concatenate(**vars(args))
