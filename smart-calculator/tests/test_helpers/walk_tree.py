from typing import List, Tuple

from calculator.core import Basic
from calculator.solver.rules import BaseSolverRule, TypicalMistake
from calculator.tree import Tree


def walk_tree_until_rule_apply(expr: Basic, rule: BaseSolverRule) -> Tuple[Tree, float, List[TypicalMistake]]:
    original_expr_hash = hash(expr)
    tree = Tree(expr)
    for nid, node in tree.expand_tree():
        if rule.root_operation == type(node) and rule.check_condition(tree, nid):
            modified_tree, cost, typical_errors = rule.apply(tree, nid)
            break
    assert hash(expr) == original_expr_hash
    return modified_tree, cost, typical_errors
