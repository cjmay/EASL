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
@mark.parametrize('update_generate, num_hits,num_items,bool_flags,overlap',
                  list(it.product((False, True), (0, 1, 30), (1, 5), ('', '--sample-var', '--na-adjust'), (0,))) +
                  list(it.product((False, True), (1, 30), (1, 5), ('--mean-windows',), (0, 2))))
def test_scripts(script_data, update_generate, num_hits, num_items, bool_flags, overlap):
    prefix = script_data['prefix']
    check_call(
        'python {script} {prefix}political.csv'.format(
            script=os.path.join('scripts', 'easl-initialize.py'),
            prefix=prefix).split())
    for round_num in range(NUM_ROUNDS):
        if (not update_generate) or round_num == 0:
            check_call(
                'python {script} generate '
                '{prefix}political_{round}.csv --hits {num_hits} --item {num_items} '
                '{bool_flags} --overlap {overlap}'.format(
                    script=os.path.join('scripts', 'easl-main.py'),
                    prefix=prefix,
                    num_hits=num_hits,
                    num_items=num_items,
                    bool_flags=bool_flags,
                    overlap=overlap,
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
            'python {script} {operation} '
            '{prefix}political_{round}.csv --item {num_items} --hits {num_hits} '
            '{bool_flags} --overlap {overlap}'.format(
                script=os.path.join('scripts', 'easl-main.py'),
                operation='update-generate' if (update_generate and round_num + 1 < NUM_ROUNDS) else 'update',
                prefix=prefix,
                num_items=num_items,
                num_hits=num_hits,
                bool_flags=bool_flags,
                overlap=overlap,
                round=round_num,
            ).strip().split())
