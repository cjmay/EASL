from subprocess import check_call
import os
import shutil
import itertools as it

from pytest import fixture, mark

from simulate_hit_results import simulate_hit_results


@fixture(params=['', 'test_experiments' + os.sep])
def script_data(request):
    prefix = request.param
    if prefix and not os.path.isdir(prefix):
        os.makedirs(prefix)
    shutil.copy('experiments/political/political.csv', os.path.join(prefix, 'political.csv'))
    yield dict(prefix=prefix)
    os.remove(os.path.join(prefix, 'political.csv'))
    os.remove(os.path.join(prefix, 'political_0.csv'))
    os.remove(os.path.join(prefix, 'political_hit_1.csv'))
    os.remove(os.path.join(prefix, 'political_result_1.csv'))
    os.remove(os.path.join(prefix, 'political_1.csv'))
    if prefix:
        os.rmdir(prefix)


@mark.parametrize('num_hits,num_items', it.product((1, 30, 900), (1, 5, 25)))
def test_scripts(script_data, num_hits, num_items):
    prefix = script_data['prefix']
    check_call(
        'python initialize.py {prefix}political.csv'.format(prefix=prefix).split())
    check_call(
        'python main.py --operation generate '
        '--model {prefix}political_0.csv --hits {num_hits} --item {num_items}'.format(
            prefix=prefix,
            num_hits=num_hits,
            num_items=num_items
        ).split())
    simulate_hit_results('{prefix}political_hit_1.csv'.format(prefix=prefix),
                         '{prefix}political_result_1.csv'.format(prefix=prefix))
    check_call(
        'python main.py --operation update '
        '--model {prefix}political_0.csv --item {num_items}'.format(
            prefix=prefix,
            num_items=num_items
        ).split())
