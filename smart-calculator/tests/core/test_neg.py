from calculator.core import Neg
from calculator.numbers import Integer


def test_neg():
    assert Neg(Integer(1)) == Neg(Integer(1))
