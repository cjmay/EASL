from pytest import raises, mark
from numpy.testing import assert_allclose

from easl import EASL


@mark.parametrize('na_count', [0, 1, 2])
def test_easl_mode(na_count):
    easl = EASL()
    assert_allclose(easl.mode(1, 1, na_count, ''), 0.5)
    assert_allclose(easl.mode(1, 2, na_count, '0'), 0)
    assert_allclose(easl.mode(2, 1, na_count, '1'), 1)
    assert_allclose(easl.mode(1.5, 1.5, na_count, '0.5'), 0.5)
    assert_allclose(easl.mode(1.5, 2.5, na_count, '0.5 1'), 0.25)
    assert_allclose(easl.mode(2.5, 1.5, na_count, '1 0.5'), 0.75)


@mark.parametrize('na_count', [0, 1, 2])
def test_easl_mode_invalid(na_count):
    easl = EASL()
    with raises(Exception):
        easl.mode(0.5, 1, na_count, '')
    with raises(Exception):
        easl.mode(0.5, 1, na_count, '')


@mark.parametrize('na_count', [0, 1, 2])
def test_easl_var(na_count):
    easl = EASL()
    assert_allclose(easl.variance(1, 1, na_count, ''), 1./12)
    assert_allclose(easl.variance(1.5, 1.5, na_count, '0.5'), 2.25 / (3 * 3 * 4))
    assert_allclose(easl.variance(1.5, 2.5, na_count, '0.5 1'), 3.75 / (4 * 4 * 5))