from .expr import Expr


class Pow(Expr):

    is_Pow = True

    def __new__(cls, p, q):
        return Expr.__new__(cls, p, q)
