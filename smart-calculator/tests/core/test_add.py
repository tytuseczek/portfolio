from calculator.core.add import Add
from calculator.core.neg import Neg


def test_add_commutative():
    assert Add(1, 2) == Add(1, 2)
    assert Add(1, 2).equals(Add(1, 2))
    assert Add(1, 2) != Add(2, 1)
    assert Add(1, 2).equals(Add(2, 1))
    assert Add(1, 2, 3, 4) != Add(4, 3, 2, 1)
    assert Add(1, 2, 3, 4).equals(Add(4, 3, 2, 1))


def test_sub_commutative():
    assert Add(1, Neg(2)) == Add(1, Neg(2))
    assert Add(1, Neg(2)) != Add(2, Neg(1))
