#!/usr/bin/env python


from easl import EASL, run


if __name__ == "__main__":
    import argparse
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--operation', dest="operation",
                            choices=["generate", "update", "update-generate"], required=True,
                            help="operation to run")
    arg_parser.add_argument('--model', dest="model_path", required=True,
                            help="model file path")
    arg_parser.add_argument('--item', dest="param_items", type=int,
                            default=EASL.DEFAULT_PARAMS['param_items'],
                            help="number of items per hit (default 5) ")
    arg_parser.add_argument('--match', dest="param_match", type=float,
                            default=EASL.DEFAULT_PARAMS['param_match'],
                            help="parameter gamma for match quality (default 0.1) ")
    arg_parser.add_argument(
        '--hits',
        dest="param_hits",
        type=int,
        default=EASL.DEFAULT_PARAMS['param_hits'],
        help="number of HITs to generate (recommend: hits = N/k, N=number of entire sample points, k=items per hit) ")
    arg_parser.add_argument('--mean-windows', dest="param_mean_windows", action='store_true',
                            help="use mean windows to compute HITs "
                                 "(default: original EASL method)")
    arg_parser.add_argument('--overlap', dest="param_overlap", type=int,
                            default=EASL.DEFAULT_PARAMS['param_overlap'],
                            help="number of items by which to overlap HITs")
    arg_parser.add_argument('--sample-var', dest="param_sample_var", action='store_true',
                            help="use sample variance with heuristic for 0, 1 samples "
                                 "(default: Beta variance heuristic)")
    arg_parser.add_argument('--na-adjust', dest="param_na_adjust", action='store_true',
                            help="reduce variance and center mode by N/A count")

    args = arg_parser.parse_args()

    run(args.operation, args.model_path, dict(**vars(args)))
