# -*- coding: utf-8 -*-

import csv
import random
import logging
import os
from csv import DictReader
from math import ceil

import numpy as np
from scipy.stats import spearmanr

from .encode_emoji import replace_emoji_characters


LOGGER = logging.getLogger(__name__)

np.random.seed(12345)
random.seed(12345)


class EASL(object):
    """
    Efficient Annotation for Scalar Labels
    """

    DEFAULT_PARAMS = dict(
        param_items=5,
        param_hits=0,
        param_match=0.1,
        param_mean_windows=False,
        param_overlap=0,
        param_sample_var=False,
        param_na_adjust=False,
    )

    def __init__(self, params=None):
        if params is None:
            params = {}

        self.params = params
        self.items = {}
        self.headerModel = []
        self.headerHits = []
        LOGGER.info("model parameters: {}".format(self.params))

    def get_param(self, param_name):
        return self.params.get(param_name, self.DEFAULT_PARAMS[param_name])

    def initItem(self, filePath):
        with open(filePath) as f:
            csvReader = csv.DictReader(f)
            self.headerModel = csvReader.fieldnames + ['alpha', 'beta', 'mode', 'var', 'na_count', 'scores']
            for row in csvReader:
                if not ('id' in row and 'sent' in row):
                    raise Exception("Columns must have at least length of two (e.g., id, sent)")

                out_row = dict(
                    alpha=1,
                    beta=1,
                    mode=0.5,
                    var=0.0833,
                    na_count=0,
                    scores='',
                )
                out_row.update(dict(
                    (k, replace_emoji_characters(v))
                    for (k, v) in row.items()
                ))
                self.items[out_row["id"]] = out_row

    def loadItem(self, filePath):
        csvReader = csv.DictReader(open(filePath, 'r'))
        self.headerModel = csvReader.fieldnames
        for _h in self.headerModel:
            for _i in range(1, self.get_param("param_items") + 1):
                self.headerHits.append(_h + str(_i))

        for row in csvReader:
            self.items[row["id"]] = row

    def saveItem(self, newModelPath):
        csvWriter = csv.DictWriter(open(newModelPath, 'w', newline=''), fieldnames=self.headerModel)
        csvWriter.writeheader()
        for row in self.items.values():
            csvWriter.writerow(row)

    def generateHits(self, filePath, hitItems):
        csvWriter = csv.DictWriter(open(filePath, 'w', newline=''), fieldnames=self.headerHits)
        csvWriter.writeheader()

        hit_item_pairs = list(hitItems.items())
        random.shuffle(hit_item_pairs)
        for itemID, compareIDs in hit_item_pairs:
            ids = [itemID] + list(compareIDs)
            random.shuffle(ids)
            rowDict = {}

            for i, id_i in enumerate(ids):
                for headerItem in self.headerModel:
                    rowDict[headerItem + str(i + 1)] = self.items[id_i][headerItem]
            csvWriter.writerow(rowDict)

    def getNextK(self, iterNum):
        k = self.get_param('param_hits')
        if not k:
            k = ceil(len(self.items) / self.get_param('param_items'))

        k_items = {}

        if iterNum == 0:
            # The first iteration will cover all items (maybe more than once).
            id_list = []
            while len(id_list) < k * self.get_param('param_items'):
                id_sublist = list(self.items.keys())
                random.shuffle(id_sublist)
                id_list += id_sublist

            for hit_start in range(0, k, self.get_param('param_items')):
                k_items[id_list[hit_start]] = id_list[hit_start + 1:
                                                      hit_start + self.get_param('param_items')]

        else:
            if self.get_param('param_mean_windows'):
                # sort items by mode
                mode_list = sorted([
                    (float(row['mode']), random.random(), row['id'])
                    for row in self.items.values()])

                # compute number of items needed to make `k` hits with
                # `self.get_param('param_items']` items per hit, where each
                # hit overlaps with its adjacent hits by `overlap` items
                overlap = self.get_param('param_overlap')
                num_items_per_hit = self.get_param('param_items')
                total_num_items_needed = k * num_items_per_hit - (k - 1) * overlap
                if total_num_items_needed > len(mode_list):
                    raise Exception(
                        'there are not enough items to generate {} hits with {} '
                        'items each and overlap {}'.format(
                            k, num_items_per_hit, overlap))

                # compute number of hits to skip at the beginning of
                # `modeList`
                start = int((len(mode_list) - total_num_items_needed) / 2)

                # create hits (`k_items` is a dictionary from the first item
                # the hit to a list of the other `k - 1` items)
                for hit_num in range(k):
                    hit_start = start + hit_num * (num_items_per_hit - overlap)
                    k_items[mode_list[hit_start][2]] = [
                        item_id
                        for (item_mode, _, item_id)
                        in mode_list[hit_start + 1:hit_start + num_items_per_hit]]
            else:
                # 1. select k different items according to variance
                var_list = []    # [(itemID, var), (itemID, var), ...]
                index_set = set([])

                for item_id, row in self.items.items():
                    var_list.append((row["id"], float(row["var"]), random.random()))
                    index_set.add(item_id)

                var_list = sorted(var_list, key=lambda x: (-x[1], x[2]))
                k_item_list = var_list[:k]

                # 2. for each k, choose m items according to matching quality
                for _k in k_item_list:
                    _j = _k[0]  # itemID
                    candidate_id = []
                    candidate_prob = []
                    sum_prob = 0.
                    m_j = float(self.items[_j]["mode"])
                    var_j = float(self.items[_j]["var"])
                    param_gamma = float(self.get_param("param_match"))

                    for _i in index_set:
                        if _i != _j:
                            m_i = float(self.items[_i]["mode"])
                            var_i = float(self.items[_i]["var"])
                            csq = 2. * param_gamma**2 + var_j + var_i
                            match_quality = np.sqrt(
                                2.0 * param_gamma**2 / csq
                            ) * np.exp(
                                -((m_j - m_i)**2) / (2.0 * csq))
                            sum_prob += match_quality
                            candidate_id.append(_i)
                            candidate_prob.append(match_quality)

                    candidate_prob = [p / sum_prob for p in candidate_prob]
                    selected_ids = np.random.choice(
                        candidate_id,
                        self.get_param("param_items") - 1,
                        p=candidate_prob,
                        replace=False)
                    k_items[_j] = selected_ids

        return k_items

    def observe(self, observe_path):
        csvReader = csv.DictReader(open(observe_path, 'r'))
        for row in csvReader:
            for _i in range(1, self.get_param("param_items") + 1):
                id_i = row["Input.id{}".format(_i)]
                if row.get("Answer.na{}".format(_i), "off").lower() == "on":
                    self.items[id_i]["na_count"] = int(self.items[id_i]["na_count"]) + 1
                else:
                    s_i = float(row["Answer.range{}".format(_i)]) / 100.
                    self.items[id_i]["alpha"] = float(self.items[id_i]["alpha"]) + s_i
                    self.items[id_i]["beta"] = float(self.items[id_i]["beta"]) + (1. - s_i)
                    self.items[id_i]["scores"] += ' {:.2f}'.format(s_i)
                self.items[id_i]["mode"] = self.mode(
                    self.items[id_i]["alpha"],
                    self.items[id_i]["beta"],
                    self.items[id_i]["na_count"],
                    self.items[id_i]["scores"])
                self.items[id_i]["var"] = self.variance(
                    self.items[id_i]["alpha"],
                    self.items[id_i]["beta"],
                    self.items[id_i]["na_count"],
                    self.items[id_i]["scores"])

    def get_scores(self):
        return dict((item['id'], item['mode']) for item in self.items.values())

    def _process_params(self, alpha, beta, na_count, scores):
        return (
            float(alpha),
            float(beta),
            int(na_count),
            [float(s) for s in scores.split()],
        )

    def mode(self, alpha, beta, na_count, scores):
        alpha, beta, na_count, scores = self._process_params(alpha, beta, na_count, scores)
        if self.get_param('param_na_adjust'):
            diff = alpha - beta
            na_count = float(na_count)
            if diff < 0:
                alpha += min(na_count, -diff)
            else:
                beta += min(na_count, diff)
            na_count -= min(na_count, abs(diff))
            alpha += na_count / 2.
            beta += na_count / 2.

        if alpha == 1. and beta == 1.:
            return 0.5
        else:
            assert alpha + beta > 2.0
            if alpha < 1.0 and beta < 1.0:
                raise Exception("alpha={}, beta={}".format(str(alpha), str(beta)))
            return (alpha - 1.0) / (alpha + beta - 2.0)

    def mean(self, alpha, beta, na_count, scores):
        alpha, beta, na_count, scores = self._process_params(alpha, beta, na_count, scores)
        return alpha / (alpha + beta)

    def variance(self, alpha, beta, na_count, scores):
        alpha, beta, na_count, scores = self._process_params(alpha, beta, na_count, scores)
        if self.get_param("param_sample_var"):
            if len(scores) == 0:
                return 1.
            elif len(scores) == 1:
                return 0.75
            else:
                return np.var(scores, ddof=1)
        elif self.get_param("param_na_adjust"):
            return (alpha * beta) / ((np.power(alpha + beta + na_count, 2.0)) * (alpha + beta + na_count + 1))
        else:
            return (alpha * beta) / ((np.power(alpha + beta, 2.0)) * (alpha + beta + 1))


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
        next_items = model.getNextK(iter_num)
        model.generateHits(hit_path, next_items)


def evaluate(model_path, gold_standard_path):
    model = EASL()
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
