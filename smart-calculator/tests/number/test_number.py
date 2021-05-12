from pytest import mark, raises

from calculator.core import Neg
from calculator.numbers import Float, Integer, Number


@mark.parametrize(
    "base, casted",
    [
        (1, Integer(1)),
        (-1, Neg(Integer(1))),
        (Integer(1), Integer(1)),
        (Integer(3.0), Integer(3)),
        ("-1.2", Neg(Float("1.2"))),
        ("1.2", Float("1.2")),
        (Number(3.3), Float("3.3")),
        (Number(15 / 5), Integer(3)),
    ],
)
def test_number(base, casted):
    assert Number(base) == casted
    assert isinstance(Number(base), type(casted))


def test_value_error():
    with raises(ValueError):
        Number("foo")


def test_type_error():
    with raises(TypeError):
        Number(None)


def test_integer_value_error():
    with raises(TypeError):
        Integer(None)
