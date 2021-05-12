from abc import ABC, abstractmethod

from calculator.tree import Tree


class Heuristic(ABC):

    weight: float = 0.0

    @classmethod
    @abstractmethod
    def estimate(cls, tree: Tree, goal: Tree) -> float:
        pass


class SimpleNodeAmountHeuristic(Heuristic):
    """Simple heuristics - compare only number of nodes"""

    weight: float = 10.0

    @classmethod
    def estimate(cls, tree: Tree, goal: Tree) -> float:
        return abs(tree.size - goal.size) * cls.weight
