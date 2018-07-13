#!/usr/bin/env python


import os

from easl import EASL


if __name__ == "__main__":
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Read data from CSV file with at least two columns '
                    '(id and sent) and write initial EASL model file for that '
                    'data (replacing .csv on the input data CSV path with '
                    '_0.csv to get the output EASL model CSV path).',
    )
    parser.add_argument('in_file_path', help='Path to input CSV file')
    args = parser.parse_args()

    dir_path = os.path.dirname(args.in_file_path)
    file_name = os.path.splitext(os.path.basename(args.in_file_path))[0]
    out_file_name = file_name + "_0" + os.extsep + "csv"
    out_file_path = os.path.join(dir_path, out_file_name)

    model = EASL()
    model.initItem(args.in_file_path)
    model.saveItem(out_file_path)
