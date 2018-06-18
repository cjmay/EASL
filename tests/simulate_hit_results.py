#!/usr/bin/env python3

from csv import DictReader, DictWriter
from random import randint


def simulate_hit_results(hit_path, results_path):
    with open(hit_path) as in_f, open(results_path, 'w', newline='') as out_f:
        num_items_per_hit = 0
        writer = None
        for in_row in DictReader(in_f):
            if writer is None:
                while 'id{}'.format(num_items_per_hit + 1) in in_row:
                    num_items_per_hit += 1
                writer = DictWriter(out_f, fieldnames=[
                    '{}{}'.format(prefix, i + 1)
                    for prefix in ('Input.id', 'Answer.range')
                    for i in range(num_items_per_hit)])
                writer.writeheader()
            out_row = dict()
            for i in range(num_items_per_hit):
                out_row['Input.id{}'.format(i + 1)] = in_row['id{}'.format(i + 1)]
                out_row['Answer.range{}'.format(i + 1)] = randint(0, 100)
            writer.writerow(out_row)


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description='Simulate HIT results, given HIT batch data.',
        formatter_class=ArgumentDefaultsHelpFormatter
    )
    parser.add_argument('hit_path', help='Path to HIT batch data CSV file')
    parser.add_argument('results_path', help='Path to HIT results CSV file')
    args = parser.parse_args()
    simulate_hit_results(args.hit_path, args.results_path)
