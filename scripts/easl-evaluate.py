#!/usr/bin/env python


from easl import evaluate


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
