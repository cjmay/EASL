from subprocess import check_call
import os
import shutil

from pytest import fixture

from simulate_hit_results import simulate_hit_results


@fixture(params=['', 'test_experiments' + os.sep])
def script_data(request):
    prefix = request.param
    remove_dir = False
    if prefix and not os.path.isdir(prefix):
        remove_dir = True
        os.makedirs(prefix)
    shutil.copy('experiments/political/political.csv', os.path.join(prefix, 'political.csv'))
    yield dict(prefix=prefix)
    os.remove(os.path.join(prefix, 'political.csv'))
    os.remove(os.path.join(prefix, 'political_0.csv'))
    os.remove(os.path.join(prefix, 'political_hit_1.csv'))
    os.remove(os.path.join(prefix, 'political_result_1.csv'))
    os.remove(os.path.join(prefix, 'political_1.csv'))
    if remove_dir:
        os.rmdir(prefix)


def test_scripts(script_data):
    prefix = script_data['prefix']
    check_call(
        'python initialize.py {prefix}political.csv'.format(prefix=prefix).split())
    check_call(
        'python main.py --operation generate --model {prefix}political_0.csv --hits 25'.format(prefix=prefix).split())
    simulate_hit_results('{prefix}political_hit_1.csv'.format(prefix=prefix),
                         '{prefix}political_result_1.csv'.format(prefix=prefix))
    check_call(
        'python main.py --operation update --model {prefix}political_0.csv'.format(prefix=prefix).split())
