from calculator.numbers import Integer

from .expr import Expr


class Nroot(Expr):

    is_Nroot = True

    def __new__(cls, p, q):

        if not isinstance(q, Integer):
            raise ValueError("Root must a positive integer")

        return Expr.__new__(cls, p, q)
