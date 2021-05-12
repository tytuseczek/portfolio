from pytest import raises

from calculator.core import Div, Neg, PrintFormat
from calculator.core.exceptions import IncorrectValueCalculatorError
from calculator.numbers import Integer, Symbol
from tests._shortcuts import One, Three, Two


def test_commutative():
    assert Div(1, 2) == Div(1, 2)
    assert Div(1, 2) != Div(2, 1)


def test_print_format_mixe_fraction_default_whole_part():
    assert Div(One, Two, print_format=PrintFormat.DIV_MIXED_FRACTION).whole_part == 0
    assert Div(Three, Two, print_format=PrintFormat.DIV_MIXED_FRACTION).whole_part == 1
    assert Div(Integer(11), Three, print_format=PrintFormat.DIV_MIXED_FRACTION).whole_part == 3
    assert Div(Integer(11), Three, print_format=PrintFormat.DIV_MIXED_FRACTION, whole_part=2).whole_part == 2


def test_print_format_raises():
    with raises(IncorrectValueCalculatorError):
        assert Div(-1, 2, print_format=PrintFormat.DIV_MIXED_FRACTION)  # int instead of Integers

    with raises(IncorrectValueCalculatorError):
        assert Div(Neg(One), Two, print_format=PrintFormat.DIV_MIXED_FRACTION)  # Negative Integer

    with raises(IncorrectValueCalculatorError):
        assert Div(Three, Two, print_format=PrintFormat.DIV_MIXED_FRACTION, whole_part=-1)  # negative whole_part

    with raises(IncorrectValueCalculatorError):
        assert Div(Three, Symbol("x"), print_format=PrintFormat.DIV_MIXED_FRACTION)  # use of Symbols

    with raises(IncorrectValueCalculatorError):
        assert Div(Three, Two, print_format=PrintFormat.DIV_MIXED_FRACTION, whole_part=2)  # whole part too big
