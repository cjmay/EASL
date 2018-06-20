#!/usr/bin/env python


from csv import DictReader

from scipy.stats import spearmanr

from easl import EASL


def evaluate(model_path, gold_standard_path):
    model = EASL({'param_items': 1})
    model.loadItem(model_path)
    model_scores_map = model.get_scores()
    ids = sorted(model_scores_map.keys())
    model_scores = [model_scores_map[id_] for id_ in ids]

    gold_labels_map = dict()
    with open(gold_standard_path) as f:
        for row in DictReader(f):
            gold_labels_map[row['id']] = float(row['label'])
    gold_labels = [gold_labels_map[id_] for id_ in ids]

    print(spearmanr(gold_labels, model_scores).correlation)


if __name__ == '__main__':
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        description='Compute and print Spearman correlation coefficient '
                    'between EASL item modes and gold standard.',
        formatter_class=ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('model_path', help='Path to EASL model file')
    parser.add_argument('gold_standard_path',
                        help='Path to gold standard CSV file (with columns '
                             'id, sent, label)')
    args = parser.parse_args()
    evaluate(args.model_path, args.gold_standard_path)
