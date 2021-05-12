from pytest import raises

from calculator.core import Add, Eq


def test_commutative():
    assert Eq(1, 2) == Eq(1, 2)
    assert Eq(1, 2).equals(Eq(1, 2))
    assert Eq(1, 2) != Eq(2, 1)
    assert Eq(1, 2).equals(Eq(2, 1))


def test_force_root():
    with raises(ValueError, match=r"Expresion of type Eq can be only in the root of the formula"):
        Add(Eq(1, 2), 3)
