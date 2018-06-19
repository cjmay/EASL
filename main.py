#!/bin/python
# -*- coding: utf-8 -*-

import os,sys
import argparse
import easl as easl


if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('--operation', dest="operation",
                            choices=["generate", "update", "update-generate"], required=True,
                            default=None, help="operation to run")
    arg_parser.add_argument('--model', dest="model_path", required=False,
                            default=None, help="model file path")
    arg_parser.add_argument('--item', dest="param_items", type=int, required=False,
                            default=5, help="number of items per hit (default 5) ")
    arg_parser.add_argument('--match', dest="param_match", type=float, required=False,
                            default=0.1, help="parameter gamma for match quality (default 0.1) ")
    arg_parser.add_argument('--hits', dest="param_hits", type=int, required=False,
                            default=20, help="number of HITs to generate (recommend: hits = N/k, N=number of entire sample points, k=items per hit) ")

    args = arg_parser.parse_args()
    params = {}
    for k, v in vars(args).items():
        params[k] = v

    model = easl.EASL(params)

    if args.operation is None:
        print("Specify operation either generate or update")
        exit(1)

    if args.model_path is None:
        print("Specify model_path")
        exit(1)

    model_path = args.model_path
    model_dir = os.path.dirname(model_path)
    #model_name = model_path.split('/')[-1].split('_')[0]
    model_name = "_".join(os.path.basename(model_path).split('_')[:-1])
    iterNum = int(os.path.splitext(os.path.basename(model_path))[0].split('_')[-1])

    if args.operation in ("update", "update-generate"):
        # update the model
        observe_path = os.path.join(model_dir, model_name + '_result_' + str(iterNum+1) + os.extsep + "csv")
        if not os.path.exists(observe_path):
            print("Mturk result file is not found. {} is expected.".format(observe_path))
            exit(1)

        new_model_path = os.path.join(model_dir, model_name + '_' + str(iterNum+1) + os.extsep + "csv")
        model.loadItem(model_path)
        model.observe(observe_path)
        model.saveItem(new_model_path)

        model_path = new_model_path
        iterNum += 1

    if args.operation in ("generate", "update-generate"):
        # generate next hits
        model.loadItem(model_path)
        hit_path = os.path.join(model_dir, model_name + '_hit_' + str(iterNum+1) + os.extsep + "csv")
        nextItems = model.getNextK(args.param_hits, iterNum)
        model.generateHits(hit_path, nextItems)