from .expr import Expr


class Add(Expr):
    is_Add = True
    is_commutative = True

    def __new__(cls, p, q, *rest):
        return Expr.__new__(cls, p, q, *rest)
