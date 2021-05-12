from typing import List, Optional, Tuple

from sympy.core.symbol import Symbol as SympySymbol
from sympy.solvers import solve_linear as sympy_solve_linear

from calculator.core import Basic
from calculator.core.exceptions import IncorrectValueCalculatorError, NotSupportedCalculatorError
from calculator.core.relational import Eq, EquationType
from calculator.numbers import Symbol
from calculator.parser.sympy_converter import basic2sympy, sympy2basic
from calculator.printer.latexprinter import LatexPrinter
from calculator.solver.rules import DEFAULT_RULES, BaseSolverRule
from calculator.solver.rules.relational.relational_divide_by_number_to_get_symbol_alone import (
    RelationalDivideByNumberToGetSymbolAlone,
)
from calculator.solver.rules.relational.relational_move_expressions_with_symbols_left_rule import (
    RelationalMoveExpressionsWithSymbolsLeftRule,
)
from calculator.solver.rules.relational.relational_move_expressions_without_symbols_right_rule import (
    RelationalMoveExpressionsWithoutSymbolsRightRule,
)
from calculator.solver.rules.relational.relational_remove_denominators_numbers import (
    RelationalRemoveDenominatorNumberRule,
)
from calculator.solver.rules.relational.relational_to_one_side_zero_rule import RelationalToOneSideZeroRule
from calculator.solver.solver import Solver
from calculator.tree import Tree

printer = LatexPrinter()

# https://github.com/sympy/sympy/blob/46e00feeef5204d896a2fbec65390bd4145c3902/sympy/solvers/solvers.py#L1984-L2165
SYMPY_NOT_DEPENDENT_RESULT = (0, 1)
SYMPY_NO_SOLUTION_RESULT = (0, 0)


def define_equation_type(expr: Basic) -> Tuple[EquationType, Optional[Basic]]:
    """
    Define equation type.
    If expected result is found in the process (e.g. using sympy), return it as a second output
    """

    if not isinstance(expr, Eq):
        raise IncorrectValueCalculatorError("Cannot define equation type: Not an equation")

    if len(expr.atoms(Symbol)) == 0:
        return (EquationType.INDEPENDENT_OF_VARIABLES, None)  # TODO: check if result is True or False

    if len(expr.atoms(Symbol)) > 1:
        return (EquationType.MULTIPLE_VARIABLES, None)

    try:
        sympy_solution = sympy_solve_linear(basic2sympy(expr))
    except TypeError:
        raise ValueError("Could not determine equation type")

    if sympy_solution == SYMPY_NOT_DEPENDENT_RESULT:
        return (EquationType.INDEPENDENT_OF_VARIABLES, None)

    if sympy_solution == SYMPY_NO_SOLUTION_RESULT:
        return (EquationType.NO_SOLUTION, None)

    elif isinstance(sympy_solution[0], SympySymbol):
        return (EquationType.ONE_VARIABLE_LINEAR, sympy2basic(sympy_solution[1]))

    else:
        return (EquationType.ONE_VARIABLE_NON_LINEAR, None)

    raise ValueError("Could not determine equation type")


def solve_equation_linear_one_variable(expr: Basic, expected_solution: Basic) -> Tuple[Tree, Solver]:
    variable = list(expr.atoms(Symbol))[0]
    goal = Eq(variable, expected_solution)

    additional_rules: List[BaseSolverRule] = [
        RelationalToOneSideZeroRule(),
        RelationalRemoveDenominatorNumberRule(),
        RelationalMoveExpressionsWithoutSymbolsRightRule(),
        RelationalMoveExpressionsWithSymbolsLeftRule(),
        RelationalDivideByNumberToGetSymbolAlone(),
    ]

    solver = Solver(Tree(expr), Tree(goal), rules=DEFAULT_RULES + additional_rules)
    found_solution = solver.solve()

    return found_solution, solver


def solve_equation(expr: Basic) -> Tuple[Tree, Solver]:
    equation_type, expected_solution = define_equation_type(expr)
    if equation_type == EquationType.ONE_VARIABLE_LINEAR:
        assert expected_solution
        return solve_equation_linear_one_variable(expr, expected_solution)

    raise NotSupportedCalculatorError("Equation type not supported")
