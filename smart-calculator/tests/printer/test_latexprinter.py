from pytest import fixture, mark, raises

from calculator.core import Add, Basic, Div, Eq, Mul, Neg, Nroot, Pow, PrintFormat
from calculator.numbers import Float, Integer, Symbol
from calculator.printer.latexprinter import LatexPrinter
from tests._shortcuts import Four, One, Three, Two


@fixture
def latex_printer():
    return LatexPrinter()


@mark.parametrize(
    "expression, latex",
    [
        (Add(One, Two), r"1+2"),
        (Add(One, Two, Three), r"1+2+3"),
        (Add(Two, Neg(One)), r"2-1"),
        (Add(Three, Neg(Two), Neg(One)), r"3-2-1"),
        (Add(Three, Neg(Add(Two, Neg(One)))), r"3-\left(2-1\right)"),
        (Mul(Two, Three), r"2 \cdot 3"),
        (Mul(Two, Three, Four), r"2 \cdot 3 \cdot 4"),
        (Neg(One), r"-1"),
        (Neg(Two), r"-2"),
        (Add(Neg(Two), Neg(Four)), r"-2-4"),
        (Add(Two, Neg(Neg(Four))), r"2-\left(-4\right)"),
        (Mul(Two, Add(Two, Three)), r"2 \cdot \left(2+3\right)"),
        (Div(Float(1.2), Float(0.1), print_format=PrintFormat.DIV_RATIONAL), r"\frac{1.2}{0.1}"),
        (Div(Float(1.2), Float(0.1), print_format=PrintFormat.DIV_COLON), r"1.2 : 0.1"),
        (Div(Float(1.2), Add(One, Two), print_format=PrintFormat.DIV_COLON), r"1.2 : \left(1+2\right)"),
        (Div(Float(1.2), Mul(One, Two), print_format=PrintFormat.DIV_COLON), r"1.2 : \left(1 \cdot 2\right)"),
        (Neg(Div(One, Two, print_format=PrintFormat.DIV_RATIONAL)), r"-\frac{1}{2}"),
        (Mul(Add(Two, Three), Four), r"\left(2+3\right) \cdot 4"),
        (Add(Two, Neg(Mul(Two, Three)), Four), r"2-2 \cdot 3+4"),
        (Div(Two, One, print_format=PrintFormat.DIV_COLON), r"2 : 1"),
        (
            Div(Div(Three, Two, print_format=PrintFormat.DIV_COLON), One, print_format=PrintFormat.DIV_COLON),
            r"3 : 2 : 1",
        ),
        (Nroot(Two, Two), r"\sqrt{2}"),
        (Nroot(Two, Three), r"\sqrt[3] {2}"),
        (Div(One, Two, print_format=PrintFormat.DIV_RATIONAL), r"\frac{1}{2}"),
        (Div(Two, Four, print_format=PrintFormat.DIV_RATIONAL), r"\frac{2}{4}"),
        (Pow(Two, Four), r"2^{4}"),
        (Pow(Pow(Two, Three), Four), r"\left(2^{3}\right)^{4}"),
        (Div(Add(One, Two), Four, print_format=PrintFormat.DIV_RATIONAL), r"\frac{1+2}{4}"),
        (
            Add(
                Two,
                Div(One, Nroot(Three, Two), print_format=PrintFormat.DIV_RATIONAL),
                Neg(Mul(Pow(Two, Four), Integer(7))),
            ),
            r"2+\frac{1}{\sqrt{3}}-2^{4} \cdot 7",
        ),
        (Add(Two, Mul(Three, Four)), r"2+3 \cdot 4"),
        (
            Mul(Add(Two, Three), Four),
            r"\left(2+3\right) \cdot 4",
        ),
        (Mul(Add(Two, Three), Mul(Four, Symbol("x"))), r"\left(2+3\right) \cdot 4x"),
        (Mul(Symbol("x"), Symbol("x")), r"x \cdot x"),
        (Mul(Symbol("x"), Symbol("y")), r"xy"),
        (Div(Float(1.2), Add(One, Neg(Two)), print_format=PrintFormat.DIV_COLON), r"1.2 : \left(1-2\right)"),
        (Mul(Four, Symbol("x"), Symbol("y")), r"4xy"),
        (Mul(Four, Mul(Symbol("x"), Symbol("y"))), r"4 \cdot xy"),
        (Add(One, Add(Two, Three)), r"1+\left(2+3\right)"),
        (Add(One, Symbol("x"), Symbol("y")), r"1+x+y"),
        (Div(Integer(7), Three, print_format=PrintFormat.DIV_MIXED_FRACTION), r"2\tfrac{1}{3}"),
        (Div(Integer(7), Three, print_format=PrintFormat.DIV_MIXED_FRACTION, whole_part=1), r"1\tfrac{4}{3}"),
        (Eq(Add(One, Symbol("x"), Symbol("y")), Symbol("y")), r"1+x+y = y"),
    ],
)
def test_operations(
    latex_printer,
    expression: Basic,
    latex: str,
):
    assert latex_printer.do_print(expression) == latex


def test_empty_printer_error(latex_printer):
    class NewBasic(Basic):
        pass

    expr = NewBasic(1, 2)
    with raises(NotImplementedError, match="No printing method defined for expression NewBasic"):
        latex_printer.do_print(expr)
