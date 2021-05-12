import calculator.numbers as nr

from . import PrintFormat
from .exceptions import IncorrectValueCalculatorError
from .expr import Expr


class Div(Expr):
    is_Div = True
    whole_part = 0

    def __new__(cls, p, q, **kwargs):

        if "print_format" not in kwargs:
            kwargs["print_format"] = PrintFormat.DIV_RATIONAL

        obj = Expr.__new__(cls, p, q, **kwargs)

        if "print_format" in kwargs and kwargs["print_format"] == PrintFormat.DIV_MIXED_FRACTION:
            if not isinstance(p, nr.Integer) or not isinstance(q, nr.Integer):
                raise IncorrectValueCalculatorError(
                    "Cannot make a mixed number. You can use only positive Integers in mixed numbers."
                )

            if "whole_part" in kwargs:
                whole_part = kwargs["whole_part"]
                if not isinstance(whole_part, int):
                    raise IncorrectValueCalculatorError(
                        "Cannot make a mixed number. Whole part in mixed number must be an integer"
                    )

                if whole_part < 0:
                    raise IncorrectValueCalculatorError(
                        "Cannot make a mixed number. Whole part in mixed number cannot be negative"
                    )

                if whole_part > p.arg // q.arg:
                    raise IncorrectValueCalculatorError(
                        "Cannot make a mixed number. Whole part in mixed number is too big"
                    )

                obj.whole_part = whole_part

            else:
                obj.whole_part = p.arg // q.arg

        return obj

    def __eq__(self, other):
        if not super().__eq__(other):
            return False
        return self.whole_part == other.whole_part

    def __hash__(self) -> int:
        return hash((super().__hash__(), self.whole_part))

    def __repr__(self):
        r = super().__repr__()
        wp = self.whole_part
        return f"{repr} {wp}" if self.print_format == PrintFormat.DIV_MIXED_FRACTION else r

    @property
    def numerator(self) -> int:
        if self.print_format == PrintFormat.DIV_MIXED_FRACTION:
            return self.args[0].arg - self.whole_part * self.args[1].arg
        else:
            return self.args[1].arg
