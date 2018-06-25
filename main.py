#!/bin/python
# -*- coding: utf-8 -*-

import os

from easl import EASL


def run(operation, model_path, params):
    if operation not in ('update', 'update-generate', 'generate'):
        raise ValueError('unknown operation {}'.format(operation))

    model = EASL(params)

    model_dir = os.path.dirname(model_path)
    model_name = "_".join(os.path.basename(model_path).split('_')[:-1])
    iter_num = int(os.path.splitext(os.path.basename(model_path))[0].split('_')[-1])

    if operation in ("update", "update-generate"):
        # update the model
        observe_path = os.path.join(model_dir, model_name + '_result_' + str(iter_num + 1) + os.extsep + "csv")
        if not os.path.exists(observe_path):
            raise Exception("Mturk result file is not found. {} is expected.".format(observe_path))

        new_model_path = os.path.join(model_dir, model_name + '_' + str(iter_num + 1) + os.extsep + "csv")
        model.loadItem(model_path)
        model.observe(observe_path)
        model.saveItem(new_model_path)

        model_path = new_model_path
        iter_num += 1

    if operation in ("generate", "update-generate"):
        # generate next hits
        model.loadItem(model_path)
        hit_path = os.path.join(model_dir, model_name + '_hit_' + str(iter_num + 1) + os.extsep + "csv")
        next_items = model.getNextK(params['param_hits'], iter_num)
        model.generateHits(hit_path, next_items)


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
