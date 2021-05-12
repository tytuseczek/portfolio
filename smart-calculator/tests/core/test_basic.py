from pytest import mark

from calculator.core import Add, Basic, Eq, Mul, Neg, Pow
from calculator.numbers import Integer, Symbol
from tests._shortcuts import One, Two, X, Y


def test_str():
    class A(Basic):
        pass

    assert str(Basic(1, 2)) == "Basic(1, 2)"
    assert str(A(1, 2)) == "A(1, 2)"
    assert str(A(1, Basic(2, 3))) == "A(1, Basic(2, 3))"
    assert str(A(1, 2, 3)) == "A(1, 2, 3)"


def test_hash():
    class A(Basic):
        pass

    assert hash(Basic(1, 2)) == hash(Basic(1, 2))
    assert hash(Basic(1, Basic(2, 3))) == hash(Basic(1, Basic(2, 3)))
    assert hash(A(1, 2)) != hash(Basic(1, 2))

    expr1 = Add(
        Mul(Integer(2), X),
        Neg(Mul(Integer(3), Pow(X, Two))),
        Neg(Integer(7)),
        Mul(Integer(7), X),
        Neg(Pow(X, Two)),
    )

    expr2 = Add(
        Mul(Integer(2), X),
        Neg(Mul(Integer(3), Pow(X, Two))),
        Neg(Integer(7)),
        Mul(Integer(7), X),
        Neg(Pow(X, Two)),
    )

    assert hash(expr1) == hash(expr2)


def test_add():
    assert Basic(1, 2) == Basic(1, 2)
    assert Basic(1, 2) != Basic(1, 3)


def test_add_with_non_basic():
    assert Basic(1, 2) != "foo"
    assert "foo" != Basic(1, 3)


def test_add_nested():
    assert Basic(1, Basic(2, 3)) == Basic(1, Basic(2, 3))
    assert Basic(1, Basic(2, 3)) != Basic(1, Basic(2, 4))


def test_add_commutative():
    class A(Basic):
        is_commutative = True

    assert A(1, 2) != A(2, 1)
    assert A(1, 2).equals(A(2, 1))


def test_add_different_classes():
    class A(Basic):
        pass

    class B(Basic):
        pass

    assert A(1, 2) == A(1, 2)
    assert B(1, 2) == B(1, 2)
    assert A(1, 2) != B(1, 2)


def test_parent():
    nested = Basic(Basic(Basic(1), 2), 3)

    assert nested.parent is None
    assert nested.args[0].parent is nested
    assert nested.args[0].args[0].parent is nested.args[0]


@mark.parametrize(
    "expr, types, expected_atoms",
    [
        (One, (), {One}),
        (Add(One, Two, One), (), {One, Two}),
        (Add(One, Two, One), (Symbol,), set()),
        (Add(One, X), (Integer,), {One}),
        (Add(One, X, Y), (Symbol,), {X, Y}),
        (Mul(Add(One, X, Y), Two), (Add,), {Add(One, X, Y)}),
        (Mul(Add(One, X, Y), Two), (Add, Symbol), {X, Y, Add(One, X, Y)}),
        (Eq(X, Add(One, Two)), (Symbol,), {X}),
    ],
)
def test_atoms(expr, types, expected_atoms):
    assert expr.atoms(*types) == expected_atoms
