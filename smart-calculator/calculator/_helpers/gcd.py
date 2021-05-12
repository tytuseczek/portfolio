from copy import deepcopy
from dataclasses import dataclass
from typing import Dict

from calculator.core.basic import Basic
from calculator.core.mul import Mul
from calculator.core.neg import Neg
from calculator.core.pow import Pow
from calculator.numbers import Integer


@dataclass
class GCD:
    """helper class for factors operations:
    - grouping factors into powers, e.x: x*x -> x^2
    - finding common factors between 2 expressions, e.x: xy^3, x^2y -> xy
    - dividing expression by its factor, e.x: xy^3, xy -> y^2
    """

    size: int  # sum of all powers
    coef: int  # 1 or -1
    factors: Dict[Basic, int]

    def expand(self, expr: Basic) -> None:
        """adds new factors to GCD, so that:
        gcd_old = GCD(expr1)
        gcd_new.expand(expr2)
        gcd_new == GCD(Mul(expr1, expr2), recursive=True)
        """

        if expr.is_Neg:
            self.coef *= -1
            self.expand(expr.arg)
            return

        if expr.is_Mul:
            for arg in expr.args:
                self.expand(arg)
            return

        if expr.is_Pow:
            assert expr.args[1].is_Integer
            size = expr.args[1].arg
            for i in range(size):
                self.expand(expr.args[0])
            return

        self.size += 1
        if expr in self.factors:
            self.factors[expr] = self.factors[expr] + 1
        else:
            self.factors[expr] = 1

    @classmethod
    def from_basic(cls, expr: Basic, recursive=False) -> "GCD":
        factors: Dict[Basic, int] = {}
        size = 0
        coef = 1

        if recursive:
            gcd = GCD(0, 1, factors)
            gcd.expand(expr)
            return gcd

        if expr.is_Neg:
            gcd_ = cls.from_basic(expr.arg)
            return GCD(gcd_.size, -1 * gcd_.coef, gcd_.factors)
        elif expr.is_Mul:
            for arg in expr.args:
                gcd_ = cls.from_basic(arg)
                size += gcd_.size
                coef = coef * gcd_.coef
                for factor, power in gcd_.factors.items():
                    if factor not in factors:
                        factors[factor] = power
                    else:
                        factors[factor] = factors[factor] + power

        elif expr.is_Pow:
            assert expr.args[1].is_Integer
            size = expr.args[1].arg
            factors[expr.args[0]] = size

        else:
            size = 1
            factors[expr] = 1

        return GCD(size, coef, factors)

    def max_common_factors(self, factors2: "GCD", limit_to_symbols=False, limit_to_same_power=False) -> "GCD":
        """Calculates common factors"""
        common_factors: Dict[Basic, int] = {}
        size = 0
        for expr1, power1 in self.factors.items():
            if limit_to_symbols and not expr1.is_Symbol:
                continue
            if expr1 in factors2.factors:
                power2 = factors2.factors[expr1]
                if expr1.is_Integer or expr1.is_Float and size <= 1:
                    continue  # do not use integers and floats as common factors
                if limit_to_same_power and power1 != power2:
                    continue

                size += min(power1, power2)
                common_factors[expr1] = min(power1, power2)

        return GCD(size, 1, common_factors)

    def reduce_(self, factors2: "GCD") -> "GCD":
        """divide self by factors2"""
        size = 0
        reduced_f: Dict[Basic, int] = {}
        for f1 in self.factors:
            if f1 in factors2.factors:
                power_diff = self.factors[f1] - factors2.factors[f1]
                if power_diff > 0:
                    reduced_f[f1] = power_diff
                    size += power_diff
            else:
                reduced_f[f1] = self.factors[f1]
                size += self.factors[f1]
        return GCD(size, self.coef, reduced_f)

    def to_basic(self):
        def factoritem_to_basic(e: Basic, power: int) -> Basic:
            if power == 1:
                return e
            else:
                return Pow(e, Integer(power))

        exprs = [factoritem_to_basic(e, power) for e, power in self.factors.items()]
        if len(exprs) == 0:
            arg: Basic = Integer(1)
        elif len(exprs) == 1:
            arg = exprs[0]
        else:
            arg = Mul(*exprs)

        if self.coef == 1:
            return arg
        else:
            return Neg(arg)

    def lcm(self, other) -> "GCD":
        """Calculate least common multiple"""
        common_factors: Dict[Basic, int] = {}
        size = 0
        other_factors = deepcopy(other.factors)

        for expr1, power1 in self.factors.items():
            # TODO: Add special method for lcm of integers
            if expr1 in other.factors:
                power2 = other.factors[expr1]

                size += max(power1, power2)
                common_factors[expr1] = max(power1, power2)
                del other_factors[expr1]
            else:
                size += power1
                common_factors[expr1] = power1

        for expr2, power2 in other_factors.items():
            size += other.factors[expr2]
            common_factors[expr2] = power2

        return GCD(size, 1, common_factors)

    def __hash__(self):
        return hash((self.coef, str(self.factors)))
