from pytest import raises

from calculator.core.neg import Neg
from calculator.core.nroot import Nroot
from calculator.numbers import Float
from tests._shortcuts import Three, Two


def test_commutative():
    assert Nroot(Two, Three) != Nroot(Three, Two)


def test_root_integer():
    with raises(ValueError, match="Root must a positive integer"):
        Nroot(Two, Neg(Two))

    with raises(ValueError, match="Root must a positive integer"):
        Nroot(Two, Float(1.5))
