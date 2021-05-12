from enum import Enum
from typing import Any, List, Optional


class PrintFormat(Enum):
    NONE = 0
    DIV_COLON = 1  # a:b
    DIV_RATIONAL = 2  # a/b
    DIV_MIXED_FRACTION = 3  # a/b


class Basic:

    is_Number = False
    is_Integer = False
    is_Float = False
    is_Symbol = False
    is_Add = False
    is_Div = False
    is_Mul = False
    is_Neg = False
    is_Nroot = False
    is_Pow = False
    is_Leaf = False
    is_Root = False  # given Expression can be only at the root (e.g. Equality)
    is_Relational = False

    is_commutative: bool = False
    _args: List[Any]

    print_format = PrintFormat.NONE

    parent: "Optional[Basic]" = None

    def __new__(cls, *args, **kwargs):
        obj = object.__new__(cls)
        obj._args = list(args)
        for arg in obj._args:
            if isinstance(arg, Basic):
                if arg.is_Root:
                    raise ValueError(
                        f"Expresion of type {arg.__class__.__name__} can be only in the root of the formula"
                    )
                arg.parent = obj

        if "print_format" in kwargs:
            obj.print_format = kwargs["print_format"]

        return obj

    @property
    def args(self) -> List[Any]:
        return self._args

    @property
    def arg(self):
        return self._args[0] if len(self._args) == 1 else None

    def __getnewargs__(self):
        return tuple(self._args)

    def equals(self, other) -> bool:
        """Mathematical equality
        Ignores print formats and order for commutative expressions

        Examples
        (2+3).equals(3+2)    True
        (2/3).equals.(2:3)   True
        """
        if not isinstance(other, type(self)):
            return False

        if self.is_commutative:
            return set(self.args) == set(other.args)
        else:
            return self.args == other.args

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False

        if self.args != other.args:
            return False

        if self.print_format != other.print_format:
            return False

        return True

    def __hash__(self) -> int:
        return hash(
            (
                type(self).__name__,
                *self._args,
                self.print_format,
            )
        )

    def __repr__(self):
        name = type(self).__name__
        args = ", ".join(map(str, self.args))

        if self.print_format != PrintFormat.NONE:
            return f"{name}({args}, pf={self.print_format.name}"
        else:
            return f"{name}({args})"

    @property
    def label(self):
        if self.is_Leaf:
            return str(self)
        else:
            return type(self).__name__

    __str__ = __repr__

    def atoms(self, *types):
        """Returns the atoms that form the current object.
        based on sympy atoms() https://www.geeksforgeeks.org/python-sympy-atoms-method/
        """
        if types:
            types = tuple([t if isinstance(t, type) else type(t) for t in types])
        nodes = preorder_traversal(self, leaves=False)
        if types:
            return {node for node in nodes if isinstance(node, types)}
        return {node for node in nodes if node.is_Leaf}


def preorder_traversal(node, leaves=True):
    yield node
    if isinstance(node, Basic) and (leaves or not node.is_Leaf):
        for arg in node.args:
            yield from preorder_traversal(arg, leaves=leaves)


def postorder_traversal(node, leaves=True):
    if isinstance(node, Basic) and (leaves or not node.is_Leaf):
        for arg in node.args:
            yield from postorder_traversal(arg, leaves=leaves)
    yield node
