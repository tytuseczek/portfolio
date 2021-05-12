from .expr import Expr


class Mul(Expr):

    is_Mul = True
    is_commutative = True

    def __new__(cls, p, q, *rest):
        return Expr.__new__(cls, p, q, *rest)
