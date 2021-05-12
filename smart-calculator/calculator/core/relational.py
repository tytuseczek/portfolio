from enum import Enum

from .expr import Expr


class EquationType(Enum):
    ONE_VARIABLE_LINEAR = 0  # Example: 2x+7 = 3x-3
    ONE_VARIABLE_NON_LINEAR = 1  # Example: x+1/x^2=7
    MULTIPLE_VARIABLES = 2  # Example: x+y=2
    INDEPENDENT_OF_VARIABLES = 3  # Example: 2+2=4
    NO_SOLUTION = 4  # Example: x/x=0


class Relational(Expr):
    is_Root = True
    is_Relational = True

    def __new__(cls, p, q, *rest):
        return Expr.__new__(cls, p, q, *rest)


class Eq(Relational):
    is_commutative = True
