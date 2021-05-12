from calculator.core.mul import Mul


def test_add_commutative():
    assert Mul(1, 2) == Mul(1, 2)
    assert Mul(1, 2).equals(Mul(1, 2))
    assert Mul(1, 2) != Mul(2, 1)
    assert Mul(1, 2).equals(Mul(2, 1))
    assert Mul(1, 2, 3, 4) != Mul(4, 3, 2, 1)
    assert Mul(1, 2, 3, 4).equals(Mul(4, 3, 2, 1))
