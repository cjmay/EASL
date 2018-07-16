from pytest import raises, mark
from numpy.testing import assert_allclose

from easl import EASL


@mark.parametrize('na_count', [0, 1, 2])
def test_mode(na_count):
    easl = EASL()
    assert_allclose(easl.mode(1, 1, na_count, ''), 0.5)
    assert_allclose(easl.mode(1, 2, na_count, '0'), 0)
    assert_allclose(easl.mode(2, 1, na_count, '1'), 1)
    assert_allclose(easl.mode(1.5, 1.5, na_count, '0.5'), 0.5)
    assert_allclose(easl.mode(1.5, 2.5, na_count, '0.5 1'), 0.25)
    assert_allclose(easl.mode(2.5, 1.5, na_count, '1 0.5'), 0.75)


@mark.parametrize('na_count', [0, 1, 2])
def test_mode_invalid(na_count):
    easl = EASL()
    with raises(Exception):
        easl.mode(0.5, 1, na_count, '')
    with raises(Exception):
        easl.mode(0.5, 1, na_count, '')


@mark.parametrize('na_count', [0, 1, 2])
def test_variance(na_count):
    easl = EASL()
    assert_allclose(easl.variance(1, 1, na_count, ''), 1./12)
    assert_allclose(easl.variance(1.5, 1.5, na_count, '0.5'), 2.25 / (3 * 3 * 4))
    assert_allclose(easl.variance(1.5, 2.5, na_count, '0.5 1'), 3.75 / (4 * 4 * 5))


@mark.parametrize('total_num_items,num_items,num_hits,expected_num_hits',
                  [(30, 7, 4, 4), (30, 7, 0, 5)])
def test_get_next_k_0(total_num_items, num_items, num_hits, expected_num_hits):
    easl = EASL({'param_items': num_items, 'param_hits': num_hits})
    item_ids = set('id{}'.format(i) for i in range(total_num_items))
    for id_ in item_ids:
        easl.items[id_] = dict(id=id_, sent='sentence for {}'.format(id_))
        easl.items[id_].update(easl.INITIAL_ITEM_STATE)

    hits = easl.get_next_k(0)

    assert len(hits) == expected_num_hits

    observed_item_ids = []
    for (anchor_item, rel_items) in hits.items():
        observed_item_ids.append(anchor_item)
        observed_item_ids += list(rel_items)
        assert len(rel_items) == num_items - 1

    assert len(observed_item_ids) == expected_num_hits * num_items
    assert len(set(observed_item_ids)) == min(total_num_items, expected_num_hits * num_items)
    assert item_ids.issuperset(observed_item_ids)
