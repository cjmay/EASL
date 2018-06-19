from subprocess import check_call
import os
import shutil
import itertools as it

from pytest import fixture, mark

from simulate_hit_results import simulate_hit_results


NUM_ROUNDS = 3


def safe_remove(path):
    if os.path.exists(path):
        os.remove(path)


@fixture(params=['', 'test_experiments' + os.sep])
def script_data(request):
    prefix = request.param
    if prefix and not os.path.isdir(prefix):
        os.makedirs(prefix)
    shutil.copy('experiments/political/political.csv', os.path.join(prefix, 'political.csv'))
    yield dict(prefix=prefix)
    safe_remove(os.path.join(prefix, 'political.csv'))
    safe_remove(os.path.join(prefix, 'political_0.csv'))
    for round_num in range(NUM_ROUNDS):
        safe_remove(os.path.join(prefix, 'political_hit_{}.csv'.format(round_num + 1)))
        safe_remove(os.path.join(prefix, 'political_result_{}.csv'.format(round_num + 1)))
        safe_remove(os.path.join(prefix, 'political_{}.csv'.format(round_num + 1)))
    if prefix:
        os.rmdir(prefix)


# Note political.csv contains 150 items so we require the parameters to satisfy
#   num_hits + num_items - 1 <= 150
# because the anchors for all num_hits HITs are removed from the candidates for
# the other (num_items - 1) items in each HIT
@mark.parametrize('num_hits,num_items', it.product((1, 30, 100), (1, 5, 25)))
def test_scripts(script_data, num_hits, num_items):
    prefix = script_data['prefix']
    check_call(
        'python initialize.py {prefix}political.csv'.format(prefix=prefix).split())
    for round_num in range(NUM_ROUNDS):
        check_call(
            'python main.py --operation generate '
            '--model {prefix}political_{round}.csv --hits {num_hits} --item {num_items}'.format(
                prefix=prefix,
                num_hits=num_hits,
                num_items=num_items,
                round=round_num,
            ).split())
        simulate_hit_results(
            '{prefix}political_hit_{next_round}.csv'.format(
                prefix=prefix,
                next_round=round_num + 1),
            '{prefix}political_result_{next_round}.csv'.format(
                prefix=prefix,
                next_round=round_num + 1))
        check_call(
            'python main.py --operation update '
            '--model {prefix}political_{round}.csv --item {num_items}'.format(
                prefix=prefix,
                num_items=num_items,
                round=round_num,
            ).split())
