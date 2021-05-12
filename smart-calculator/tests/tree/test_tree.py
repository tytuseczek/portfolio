from copy import deepcopy

from calculator.core import Add, Basic, Div, Mul
from calculator.numbers import Integer, Symbol
from calculator.tree import Tree


def test_init():
    exp1 = Add(Mul(Integer(1), Integer(2)), Div(Integer(3), Integer(4)))
    tree = Tree(exp1)

    assert tree.size == 7


def test_deepcopy():
    exp1 = Add(Div(Basic(Integer(1)), Integer(2)), Integer(3))
    exp2 = deepcopy(exp1)
    tree1 = Tree(exp1)
    tree2 = Tree(exp2)
    tree3 = deepcopy(tree1)

    assert exp1 == exp2
    assert not set(tree1._nodes).intersection(set(tree2._nodes))

    assert tree3.root == exp1
    assert set(tree3._nodes) == set(Tree(tree3.root)._nodes)


def test_subtree():
    exp1 = Add(Mul(Integer(1), Integer(2)), Div(Integer(3), Integer(4)))
    tree1 = Tree(exp1)
    tree2 = tree1.subtree(tree1.root_nid)
    tree3 = tree1.subtree(tree1.root_nid, deep=True)

    assert tree1.get_node(tree1.root_nid) == tree2.get_node(tree2.root_nid) == tree3.get_node(tree3.root_nid)
    assert set(tree1._nodes) == set(tree2._nodes)
    assert not set(tree2._nodes).intersection(set(tree3._nodes))


def test_leaves():
    exp1 = Add(Mul(Integer(1), Integer(2)), Div(Integer(3), Symbol("x")))
    tree = Tree(exp1)
    assert (
        set(tree.leaves()) == set(tree.leaves(nid=tree.root_nid)) == {Integer(1), Integer(2), Integer(3), Symbol("x")}
    )


def test_tree_string():
    exp1 = Add(Mul(Integer(1), Integer(2)), Div(Integer(3), Symbol("x")))
    tree = Tree(exp1)

    tree_string_exp = (
        ""
        "Add\n"
        "|-- Mul\n"
        "|   |-- Integer(1)\n"
        "|   +-- Integer(2)\n"
        "+-- Div\n"
        "    |-- Integer(3)\n"
        "    +-- Symbol(x)\n"
    )

    assert tree.tree_string() == tree_string_exp
