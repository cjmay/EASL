#!/usr/bin/env python


from easl import EASL, run


if __name__ == "__main__":
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    parser = ArgumentParser(
        formatter_class=ArgumentDefaultsHelpFormatter,
        description='Read EASL model from specified file and either '
                    '`generate` a HIT batch CSV file from that model, '
                    '`update` the model with HIT results (in CSV format), or '
                    '`update-generate` (first update the model, then '
                    'generate new HITs).',
    )
    parser.add_argument('operation',
                        choices=["generate", "update", "update-generate"],
                        help="operation to run")
    parser.add_argument('model_path',
                        help="model file path")
    parser.add_argument('--item', dest="param_items", type=int,
                        default=EASL.DEFAULT_PARAMS['param_items'],
                        help="number of items per hit (default 5) ")
    parser.add_argument('--match', dest="param_match", type=float,
                        default=EASL.DEFAULT_PARAMS['param_match'],
                        help="parameter gamma for match quality (default 0.1) ")
    parser.add_argument('--hits', dest="param_hits", type=int,
                        default=EASL.DEFAULT_PARAMS['param_hits'],
                        help="number of HITs to generate (recommend: "
                             "hits = N/k, N=number of entire sample points, "
                             "k=items per hit)")
    parser.add_argument('--mean-windows', dest="param_mean_windows", action='store_true',
                        help="use mean windows to compute HITs "
                             "(default: original EASL method)")
    parser.add_argument('--overlap', dest="param_overlap", type=int,
                        default=EASL.DEFAULT_PARAMS['param_overlap'],
                        help="number of items by which to overlap HITs")
    parser.add_argument('--sample-var', dest="param_sample_var", action='store_true',
                        help="use sample variance with heuristic for 0, 1 samples "
                             "(default: Beta variance heuristic)")
    parser.add_argument('--na-adjust', dest="param_na_adjust", action='store_true',
                        help="reduce variance and center mode by N/A count")

    args = parser.parse_args()

    run(args.operation, args.model_path, dict(**vars(args)))
