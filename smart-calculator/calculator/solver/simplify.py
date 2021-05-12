from logging import getLogger
from typing import Tuple

from calculator.core import Basic
from calculator.core.exceptions import (
    IncorrectValueCalculatorError,
    InternalLatexParsingCalculatorError,
    LatexParsingCalculatorError,
    NotSupportedCalculatorError,
    UnableToFindSolutionCalculatorError,
    UnexpectedCalculatorError,
)
from calculator.parser.latex import parse_latex
from calculator.parser.sympy_converter import basic2sympy, sympy2basic
from calculator.printer.latexprinter import LatexPrinter
from calculator.tree import Tree

from .solve_equation import solve_equation
from .solver import SimplificationResult, Solver

logger = getLogger(__name__)
printer = LatexPrinter()


def simplify_expr(expr1: Basic) -> Tuple[Tree, Solver]:
    """simplifies a solution using sympy and then finds pedagogical path to that solution"""
    if expr1.is_Relational:
        return solve_equation(expr1)

    sympy_expr = basic2sympy(expr1)
    simplified_sympy_expr = sympy_expr.simplify()
    expr2 = sympy2basic(simplified_sympy_expr)
    tree1 = Tree(expr1)
    tree2 = Tree(expr2)
    solver = Solver(tree1, tree2)
    found_solution = solver.solve()
    return found_solution, solver


def simplify_formula(latex: str) -> SimplificationResult:

    logger.info("Simplify formula", extra={"formula": latex})
    try:
        expr = parse_latex(latex)
    except InternalLatexParsingCalculatorError:
        logger.exception("Latex parsing error.", extra={"formula": latex})
        raise LatexParsingCalculatorError("Cannot parse latex formula. Check if it is correct")
    except IncorrectValueCalculatorError:
        logger.exception("Incorrect value.", extra={"formula": latex})
        raise
    except (ValueError, TypeError, AssertionError, NotImplementedError):
        error_msg = "Unexpected calculator error."
        logger.exception(error_msg, extra={"formula": latex})
        raise UnexpectedCalculatorError(error_msg)

    try:
        found_solution, solver = simplify_expr(expr)
        return solver.get_solution_steps(found_solution)
    except NotSupportedCalculatorError:
        logger.exception("Operation not supported.", extra={"formula": latex})
        raise
    except UnableToFindSolutionCalculatorError:
        logger.exception("Unable to find solution.", extra={"formula": latex})
        raise
    except (InternalLatexParsingCalculatorError, ValueError, TypeError, AssertionError, NotImplementedError):
        error_msg = "Unexpected calculator error."
        logger.exception(error_msg, extra={"formula": latex})
        raise UnexpectedCalculatorError(error_msg)
