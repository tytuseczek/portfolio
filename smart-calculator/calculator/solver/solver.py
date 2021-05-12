from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Type

from sortedcontainers import SortedList

from calculator.core.exceptions import UnableToFindSolutionCalculatorError
from calculator.printer.latexprinter import LatexPrinter
from calculator.solver.rules import DEFAULT_RULES, BaseSolverRule
from calculator.tree import Tree

from .heuristics import SimpleNodeAmountHeuristic
from .rules.typical_mistake import TypicalMistake

printer = LatexPrinter()


@dataclass()
class SimplificationResultMistake:
    type: str
    value: str


@dataclass()
class SimplificationResultStep:
    rule_name: str
    formula: str
    typical_mistakes: List[SimplificationResultMistake]


@dataclass()
class SimplificationResult:
    steps: List[SimplificationResultStep]


class SolutionStep(object):
    def __init__(
        self,
        tree: Tree,
        cost: float,
        h: float,
        nr: int,  # number of first occurence in the solution
        step_before: "SolutionStep" = None,
        rule_before: BaseSolverRule = None,
        nid_before: int = None,
        typical_mistakes: List[TypicalMistake] = [],
    ):
        self.tree = tree
        self.root_hash = hash(tree.root)
        self.cost = cost
        self.h = h
        self.priority = cost + h
        self.step_before: Optional["SolutionStep"] = step_before
        self.rule_before = rule_before
        self.nid_before = nid_before
        self.visited_operations: Dict[str, Tuple[bool, List[int]]] = {}
        self.fully_visited = False
        self.nr = nr
        self.typical_mistakes: List[TypicalMistake] = typical_mistakes

    def __eq__(self, other):
        return self.root_hash == other.root_hash  # TODO: think about exact comparison (self.root == other.root)

    def __lt__(self, other):
        return self.priority < other.priority


@dataclass
class PathStep:
    tree_current: Tree
    tree_before: Tree
    rule: Type[BaseSolverRule]
    nid_before_changed: int
    cost: float
    heuristics: float
    typical_mistakes: List[TypicalMistake]


class Solver(object):
    def __init__(self, start: Tree, goal: Tree, rules=DEFAULT_RULES):
        self.heuristic = SimpleNodeAmountHeuristic
        self.start = start
        self.goal = goal
        cost = 0.0
        h = self.heuristic.estimate(start, goal)
        self.nr_steps_made: int = 0
        solution = SolutionStep(start, cost, h, self.nr_steps_made)
        self.steps = SortedList([solution])
        self.solution_hash_dict = {solution.root_hash: solution}
        self.rules = sorted(
            rules,
            key=lambda x: x.cost,
        )

        self.stats = {
            "operations_checked": 0,
            "operations_applied": 0,
        }
        self.history: List[Tuple[str, str, float, float, float]] = []

    def solve(self) -> Tree:

        if self.start == self.goal:
            return self.start

        while True:
            current_step, current_rule, current_nid = self._suggest_next_step()

            if current_step is None:
                raise UnableToFindSolutionCalculatorError(
                    "We tried all possible operations and could not find solution."
                )

            current_tree = current_step.tree

            self.stats["operations_applied"] += 1
            current_hash = hash(current_tree.root)
            new_tree, operation_cost, typical_mistakes = current_rule.apply(current_tree, current_nid)
            new_tree_cost = current_step.cost + operation_cost
            assert hash(current_tree.root) == current_hash  # Added to ensure that trees are not mutable
            self._update(new_tree, new_tree_cost, current_tree, current_rule, current_nid, typical_mistakes)

            if new_tree.root.equals(self.goal.root):
                return new_tree

    def get_best_path(self, tree: Tree) -> List[PathStep]:
        """get path (as lit of operations) from beginning to a given tree in the forest"""

        step = self.solution_hash_dict[hash(tree.root)]
        operations: List[PathStep] = []

        while step.step_before:
            tree_before = step.step_before
            assert step.rule_before is not None
            assert step.nid_before is not None
            operations.append(
                PathStep(
                    step.tree,
                    tree_before.tree,
                    step.rule_before.__class__,
                    step.nid_before,
                    step.cost,
                    step.h,
                    step.typical_mistakes,
                )
            )
            step = tree_before
        operations.reverse()
        return operations

    def get_solution_steps(self, tree: Tree) -> SimplificationResult:
        path = self.get_best_path(tree)
        steps: List[SimplificationResultStep] = []
        for step in path:
            typical_mistakes = [
                SimplificationResultMistake(type=m.name, value=printer.do_print(m.full_error_expr))
                for m in step.typical_mistakes
            ]

            steps.append(
                SimplificationResultStep(
                    rule_name=step.rule.__name__,
                    formula=printer.do_print(step.tree_current.root),
                    typical_mistakes=typical_mistakes,
                )
            )
        return SimplificationResult(steps=steps)

    def _suggest_next_step(
        self,
    ) -> Tuple[
        SolutionStep, BaseSolverRule, int
    ]:  # TODO: change to prefer nodes around nodes that were modified in the previous step
        for step in self.steps:
            if step.fully_visited:
                continue
            for rule in self.rules:
                rule_name = type(rule).__name__
                if rule_name not in step.visited_operations:
                    step.visited_operations[rule_name] = []
                else:
                    continue
                for nid, node in step.tree.expand_tree():
                    node_type = type(node)
                    if node_type == rule.root_operation and nid not in step.visited_operations[rule_name]:
                        step.visited_operations[rule_name].append(nid)
                        self.stats["operations_checked"] = self.stats["operations_checked"] + 1
                        if rule.check_condition(step.tree, nid):
                            return step, rule, nid
            step.fully_visited = True
        raise UnableToFindSolutionCalculatorError("We tried all possible operations and could not find solution.")

    def _update(
        self,
        new_tree: Tree,
        new_tree_cost: float,
        tree_before: Tree,
        rule_before: BaseSolverRule,
        nid_before: int,
        typical_mistakes: List[TypicalMistake],
    ) -> None:
        """Add new calculated element to the path or, if it already exists update the cost"""
        root_hash = hash(new_tree.root)
        h = self.heuristic.estimate(new_tree, self.goal)

        if root_hash in self.solution_hash_dict:
            existing_step = self.solution_hash_dict[root_hash]
            if existing_step.priority <= new_tree_cost + h:
                return None
            raise UnableToFindSolutionCalculatorError("Finding solution was too difficult.")

        history_entry = (
            printer.do_print(new_tree.root),
            rule_before.__class__.__name__,
            new_tree_cost,
            h,
            new_tree_cost + h,
        )
        self.history.append(history_entry)

        step_before = self.solution_hash_dict[hash(tree_before.root)]
        self.nr_steps_made += 1
        step = SolutionStep(
            new_tree, new_tree_cost, h, self.nr_steps_made, step_before, rule_before, nid_before, typical_mistakes
        )
        self.steps.add(step)
        self.solution_hash_dict[step.root_hash] = step
