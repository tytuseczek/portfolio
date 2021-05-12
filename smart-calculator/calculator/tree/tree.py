from copy import deepcopy
from typing import Any, Dict, Iterator, List, Optional, Tuple

from calculator.core import Basic
from calculator.core.basic import preorder_traversal


class Tree:
    """based on treelib Tree class"""

    def __init__(self, exp: Basic):
        self._nodes: Dict[int, Basic] = {}

        self.root_nid: int = id(exp)

        for e in preorder_traversal(exp, leaves=False):
            self._nodes[id(e)] = e

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Tree):
            raise TypeError("Cannot compare trees to other types")

        return self.root == other.root

    @property
    def root(self):
        return self._nodes[self.root_nid]

    def contains(self, nid: int) -> bool:
        """Check if the tree contains node of given id"""
        return nid in self._nodes

    def get_node(self, nid: int) -> Basic:
        """
        Get the object of the node with ID of ``nid``.
        """
        return self._nodes[nid]

    @property
    def size(self) -> int:
        return len(self._nodes)

    def subtree(self, nid: int, deep=False) -> "Tree":
        """
        Return a shallow or deep COPY of subtree with nid being the new root.
        """
        if not self.contains(nid):
            raise ValueError("Tree does not contain given node")

        if deep:
            return Tree(deepcopy(self._nodes[nid]))
        else:
            return Tree(self._nodes[nid])

    def expand_tree(self, nid: Optional[int] = None) -> Iterator[Tuple[int, Basic]]:
        if nid is None:
            nid = self.root_nid
        node = self._nodes[nid]
        yield nid, node
        if isinstance(node, Basic) and not node.is_Leaf:
            for arg in node.args:
                yield from self.expand_tree(id(arg))

    def leaves(self, nid: int = None) -> List[Basic]:
        """Get leaves of the whole tree or a subtree."""
        leaves = []
        if nid is None:
            for node in self._nodes.values():
                if node.is_Leaf:
                    leaves.append(node)
        else:
            for node_id, node in self.expand_tree(nid):
                if node.is_Leaf:
                    leaves.append(self._nodes[node_id])
        return leaves

    def tree_string(self, nid: int = None) -> str:
        nid = self.root_nid if (nid is None) else nid

        s = ""
        level = 0
        node = self._nodes[nid]

        dt_vline, dt_line_box, dt_line_cor = ("|", "|-- ", "+-- ")

        def node_string_iter(node, level, is_last):
            if level == 0:
                yield "", node
            else:
                leading = "".join(map(lambda x: dt_vline + " " * 3 if not x else " " * 4, is_last[0:-1]))
                lasting = dt_line_cor if is_last[-1] else dt_line_box
                yield leading + lasting, node

            if not node.is_Leaf:
                children = node.args
                idxlast = len(children) - 1
                level += 1
                for idx, child in enumerate(children):
                    is_last.append(idx == idxlast)
                    for item in node_string_iter(child, level, is_last):
                        yield item
                    is_last.pop()

        for pre, node in node_string_iter(node, level, []):
            label = node.label
            s += "{0}{1}".format(pre, label) + "\n"
        return s

    def __deepcopy__(self, memo):
        exp = deepcopy(self.root, memo)
        result = Tree(exp)
        memo[id(self)] = result
        return result

    def mutate_node(self, nid: int, new_node: Basic) -> "Tree":

        node = self.get_node(nid)
        new_exp = _mutate_tree(self.root, node, new_node)
        new_tree = Tree(new_exp)
        return new_tree


def _mutate_tree(tree: Basic, node: Basic, new_node: Basic) -> Basic:
    if tree is node:
        return new_node

    if isinstance(tree, Basic):
        return type(tree)(*[_mutate_tree(n, node, new_node) for n in tree.args])

    return tree
