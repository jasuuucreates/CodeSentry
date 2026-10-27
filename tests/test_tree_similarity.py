"""Tree edit distance and structural similarity (contract section 5)."""
import random

from engine.models import Node
from engine.tree_similarity import (canonical_order, levenshtein, structural_similarity, subtree_bag_similarity,
                                    ted_similarity, tree_size, zhang_shasha)


def n(label, *children):
    return Node(label, list(children))


def test_identical_trees_have_distance_zero():
    tree = n("f", n("a"), n("b", n("c")))
    assert zhang_shasha(tree, n("f", n("a"), n("b", n("c")))) == 0


def test_single_relabel_insert_and_delete():
    assert zhang_shasha(n("a"), n("b")) == 1                       # relabel
    assert zhang_shasha(n("a"), n("a", n("b"))) == 1               # insert one leaf
    assert zhang_shasha(n("a", n("b", n("c"))), n("a")) == 2       # delete two nodes
    assert zhang_shasha(n("a", n("b"), n("c")), n("a", n("c"))) == 1


def test_classic_zhang_shasha_example():
    # Zhang & Shasha (1989): f(d(a, c(b)), e) -> f(c(d(a, b)), e) costs 2 unit operations
    t1 = n("f", n("d", n("a"), n("c", n("b"))), n("e"))
    t2 = n("f", n("c", n("d", n("a"), n("b"))), n("e"))
    assert zhang_shasha(t1, t2) == 2
    assert zhang_shasha(t2, t1) == 2


def test_levenshtein():
    kitten = [ord(c) for c in "kitten"]
    sitting = [ord(c) for c in "sitting"]
    assert levenshtein(kitten, sitting) == 3
    assert levenshtein([], [1, 2, 3]) == 3
    assert levenshtein([1, 2, 3], [1, 2, 3]) == 0
    rng = random.Random(1)
    a = [rng.randrange(5) for _ in range(300)]
    b = a[:150] + [9] + a[150:]
    assert levenshtein(a, b) == 1


def test_ted_similarity_methods():
    tree = n("Program", n("Function", n("Return", n("Const"))))
    assert ted_similarity(tree, tree) == (1.0, "zhang-shasha")
    big = n("Program", *[n("Assign", n("Var"), n("Const")) for _ in range(100)])
    similarity, method = ted_similarity(big, big, node_cap=50)
    assert method == "preorder-sequence-approximation"
    assert similarity == 1.0


def test_canonical_order_makes_function_order_irrelevant():
    f1 = n("Function", n("Params"), n("Return", n("Var")))
    f2 = n("Function", n("Loop", n("Var"), n("Block", n("AugAssign"))))
    a = n("Program", f1, f2)
    b = n("Program", f2, f1)
    assert [c.label for c in canonical_order(a).children] == [c.label for c in canonical_order(b).children]
    result = structural_similarity(a, b)
    assert result["structure"] == 1.0
    assert set(result) == {"structure", "ted", "subtree", "method", "a_nodes", "b_nodes"}


def test_subtree_bag_similarity():
    a = n("Program", n("Assign", n("Var"), n("Const")))
    assert subtree_bag_similarity(a, a) == 1.0
    b = n("Program", n("Loop", n("Compare"), n("Block")))
    assert subtree_bag_similarity(a, b) < 0.5


def test_deep_trees_do_not_hit_recursion_limit():
    deep_a = n("Program")
    node = deep_a
    for _ in range(3000):
        child = n("If")
        node.children.append(child)
        node = child
    deep_b = n("Program")
    node = deep_b
    for _ in range(2990):
        child = n("If")
        node.children.append(child)
        node = child
    assert tree_size(deep_a) == 3001 and deep_a.size() == 3001
    result = structural_similarity(deep_a, deep_b, node_cap=200)
    assert result["method"] == "preorder-sequence-approximation"
    assert 0.9 < result["ted"] <= 1.0
