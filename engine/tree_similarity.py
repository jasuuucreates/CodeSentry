"""How similar are two program skeletons?

Two complementary measures are combined:

* **Tree edit distance** (Zhang & Shasha, 1989): the smallest number of single-node inserts,
  deletes and relabels that turn one tree into the other. It sees the global shape of the
  program, including where each construct sits.
* **Bag of subtrees**: every subtree is hashed and the two multisets of hashes are compared with
  a multiset Jaccard index. It rewards shared building blocks (a whole loop, a whole function)
  wherever they appear, so moving code around costs little.

Before comparing, the top-level definitions of each file are put into a canonical order,
because the order in which functions are written does not change what a program does.

Every traversal uses an explicit stack, so deeply nested code cannot exceed Python's recursion
limit. See docs/ARCHITECTURE_CONTRACT.md, section 5.
"""
from __future__ import annotations

import hashlib
from collections import Counter

from .models import Node


def tree_size(node: Node) -> int:
    """Number of nodes in the tree rooted at `node`."""
    return node.size()


# ---------------------------------------------------------------------------------------------
# Subtree hashing and canonical order
# ---------------------------------------------------------------------------------------------

def _subtree_hash_list(root: Node) -> list[str]:
    """Hash of every subtree of `root`, in post-order (so the last item is the root's hash).

    hash(node) = blake2b-8 hex of ``label + "(" + ",".join(child hashes in order) + ")"``.
    Because a hash is built from the children's hashes, two subtrees get the same hash exactly
    when they have the same labels in the same shape (barring an astronomically unlikely
    collision of 64-bit hashes).
    """
    hashes: list[str] = []
    finished: list[str] = []  # hashes of completed subtrees whose parent is not finished yet
    stack: list[tuple[Node, bool]] = [(root, False)]
    while stack:
        node, children_done = stack.pop()
        if not children_done:
            stack.append((node, True))
            stack.extend((child, False) for child in reversed(node.children))
            continue
        # The children were completed in order just before this node, so their hashes are the
        # last len(children) entries of `finished`.
        count = len(node.children)
        if count:
            child_hashes = finished[-count:]
            del finished[-count:]
        else:
            child_hashes = []
        text = node.label + "(" + ",".join(child_hashes) + ")"
        digest = hashlib.blake2b(text.encode("utf-8"), digest_size=8).hexdigest()
        finished.append(digest)
        hashes.append(digest)
    return hashes


def subtree_hashes(node: Node) -> Counter[str]:
    """Multiset of the hashes of all subtrees of `node` (one entry per node)."""
    return Counter(_subtree_hash_list(node))


def canonical_order(node: Node) -> Node:
    """Return a new tree whose root's children are sorted by their subtree hash.

    Definition order at the top level of a file (which function comes first) does not change
    what the program does, so reordering functions must not change the structural score.
    Deeper levels keep their original order because there the order of statements matters.

    The original tree is not modified. The child subtrees are shared with it rather than copied:
    skeletons are never mutated after they are built, and copying them for every compared pair
    would only cost time.
    """
    ordered = sorted(node.children, key=lambda child: _subtree_hash_list(child)[-1])
    return Node(node.label, ordered)


# ---------------------------------------------------------------------------------------------
# Zhang-Shasha tree edit distance
# ---------------------------------------------------------------------------------------------

def _postorder(root: Node, label_ids: dict[str, int]) -> tuple[list[int], list[int]]:
    """Number the nodes of a tree in post-order.

    Returns two parallel lists indexed by post-order number: the integer id of each node's label
    (comparing small ints is faster than comparing strings) and the post-order number of each
    node's leftmost leaf descendant, ``l(i)`` in the paper. The subtree of node i is exactly the
    nodes ``l(i) .. i``.
    """
    labels: list[int] = []
    leftmost: list[int] = []
    # Frame: [node, index of the next child to visit, leftmost leaf of the first child or -1].
    stack: list[list] = [[root, 0, -1]]
    while stack:
        frame = stack[-1]
        node, next_child = frame[0], frame[1]
        if next_child < len(node.children):
            frame[1] = next_child + 1
            stack.append([node.children[next_child], 0, -1])
            continue
        stack.pop()
        number = len(labels)
        leaf = frame[2] if frame[2] >= 0 else number  # a leaf is its own leftmost leaf
        labels.append(label_ids.setdefault(node.label, len(label_ids)))
        leftmost.append(leaf)
        if stack and stack[-1][1] == 1:
            # This node was its parent's first child, so it shares the parent's leftmost leaf.
            stack[-1][2] = leaf
    return labels, leftmost


def _keyroots(leftmost: list[int]) -> list[int]:
    """Key roots in increasing order: for each distinct leftmost leaf, the highest node having it.

    These are the root and every node that has a left sibling. Solving the forest sub-problems
    of the key roots in increasing order computes every subtree distance the algorithm needs.
    """
    seen: set[int] = set()
    roots: list[int] = []
    for number in range(len(leftmost) - 1, -1, -1):
        if leftmost[number] not in seen:
            seen.add(leftmost[number])
            roots.append(number)
    roots.reverse()
    return roots


def zhang_shasha(a: Node, b: Node) -> int:
    """Tree edit distance between two ordered labelled trees, unit cost per insert/delete/relabel.

    Classic Zhang & Shasha (1989) dynamic programme. For every pair of key roots (i, j) it fills
    a forest-distance table ``fd`` over the nodes ``l(i)..i`` of A and ``l(j)..j`` of B::

        fd[x][y] = min(fd[x-1][y] + 1,     # delete node x of A
                       fd[x][y-1] + 1,     # insert node y of B
                       match)
        match = fd[x-1][y-1] + (label_x != label_y)   if x and y are on the leftmost paths of
                                                      i and j; this also yields td[x][y]
              = fd[l(x)-1][l(y)-1] + td[x][y]         otherwise (a subtree distance found earlier)

    Time O(|A| |B| min(depth_A, leaves_A) min(depth_B, leaves_B)), memory O(|A| |B|).

    This is the hot path of the structural stage, so the inner loops avoid anything Python
    does slowly: labels are small integers, everything the loop needs is bound to local
    variables, per-column facts of B are precomputed once per key root, rows are built by
    appending, and ``min()`` calls are replaced by plain comparisons.
    """
    label_ids: dict[str, int] = {}
    labels_a, leftmost_a = _postorder(a, label_ids)
    labels_b, leftmost_b = _postorder(b, label_ids)
    if labels_a == labels_b and leftmost_a == leftmost_b:
        # Post-order labels plus leftmost leaves determine an ordered tree completely, so the
        # trees are identical (a common case for copied submissions).
        return 0

    keyroots_b = _keyroots(leftmost_b)
    # tree_dist[r][c] = edit distance between the subtree of A rooted at r and that of B at c.
    tree_dist = [[0] * len(labels_b) for _ in labels_a]

    for i in _keyroots(leftmost_a):
        li = leftmost_a[i]
        for j in keyroots_b:
            lj = leftmost_b[j]
            columns = range(lj, j + 1)
            column_labels = labels_b[lj:j + 1]
            # Offset of each column's leftmost leaf inside this forest; 0 means the column node
            # lies on the leftmost path of j (its subtree starts where j's does).
            column_offsets = [leftmost_b[c] - lj for c in columns]

            previous = list(range(j - lj + 2))  # row 0: build the forest of B by inserts
            rows = [previous]
            for x, r in enumerate(range(li, i + 1), 1):
                label_r = labels_a[r]
                dist_r = tree_dist[r]
                row_offset = leftmost_a[r] - li
                row = [x]  # column 0: delete the forest of A
                append = row.append
                left = x
                if row_offset == 0:
                    diagonal = previous[0]
                    for up, label_c, q, c in zip(previous[1:], column_labels, column_offsets, columns):
                        if q:
                            # fd[0][q] is q (q inserts), plus the known subtree distance.
                            best = q + dist_r[c]
                            if up + 1 < best:
                                best = up + 1
                            if left + 1 < best:
                                best = left + 1
                        else:
                            # Both nodes start their forests: a new subtree distance.
                            best = diagonal + (label_r != label_c)
                            if up + 1 < best:
                                best = up + 1
                            if left + 1 < best:
                                best = left + 1
                            dist_r[c] = best
                        append(best)
                        left = best
                        diagonal = up
                else:
                    offset_row = rows[row_offset]
                    for up, q, c in zip(previous[1:], column_offsets, columns):
                        best = offset_row[q] + dist_r[c]
                        if up + 1 < best:
                            best = up + 1
                        if left + 1 < best:
                            best = left + 1
                        append(best)
                        left = best
                rows.append(row)
                previous = row
    return tree_dist[-1][-1]


# ---------------------------------------------------------------------------------------------
# Bit-parallel Levenshtein distance (approximation path for large trees)
# ---------------------------------------------------------------------------------------------

def levenshtein(a: list[int], b: list[int]) -> int:
    """Edit distance between two integer sequences (unit-cost insert, delete, substitute).

    Myers (1999) / Hyyro (2003) bit-parallel algorithm. Instead of storing one column of the
    dynamic-programming table as a list of numbers, it stores only whether each cell is one more
    (``pv``) or one less (``mv``) than the cell above it, one bit per row. A whole column is then
    updated with a handful of AND/OR/XOR/shift/add operations. Python integers have unlimited
    size, so one integer holds the bits of any sequence length and the work per column is a few
    big-integer operations instead of a Python loop over every row.
    """
    if len(a) < len(b):
        a, b = b, a
    # `b` (the shorter sequence) defines the bit positions; `a` is scanned item by item.
    m = len(b)
    if m == 0:
        return len(a)

    match_masks: dict[int, int] = {}  # bit k set when b[k] equals the item
    for position, item in enumerate(b):
        match_masks[item] = match_masks.get(item, 0) | (1 << position)

    mask = (1 << m) - 1
    last_bit = 1 << (m - 1)
    pv, mv = mask, 0   # the first column is 0, 1, 2, ..., m: every step goes up by one
    distance = m
    for item in a:
        eq = match_masks.get(item, 0)
        xv = eq | mv
        xh = (((eq & pv) + pv) ^ pv) | eq
        ph = mv | (~(xh | pv) & mask)
        mh = pv & xh
        # The bottom cell of the column is the distance so far; track its change.
        if ph & last_bit:
            distance += 1
        elif mh & last_bit:
            distance -= 1
        # Shifting in a 1 for ph encodes the top row 0, 1, 2, ... of the full edit distance.
        ph = ((ph << 1) | 1) & mask
        mh = (mh << 1) & mask
        pv = mh | (~(xv | ph) & mask)
        mv = ph & xv
    return distance


def _preorder_labels(root: Node, label_ids: dict[str, int]) -> list[int]:
    """Label ids of the tree in pre-order (parent before children, children left to right)."""
    sequence: list[int] = []
    stack = [root]
    while stack:
        node = stack.pop()
        sequence.append(label_ids.setdefault(node.label, len(label_ids)))
        stack.extend(reversed(node.children))
    return sequence


# ---------------------------------------------------------------------------------------------
# Similarity scores
# ---------------------------------------------------------------------------------------------

def ted_similarity(a: Node, b: Node, node_cap: int = 200) -> tuple[float, str]:
    """Tree-edit-distance similarity in [0, 1] and the name of the method used.

    Small trees (both at most `node_cap` nodes) use exact Zhang-Shasha:
    ``1 - distance / max(|A|, |B|)``.

    Larger trees would take too long, so they use the Levenshtein distance between the
    pre-order label sequences of the two trees: ``1 - distance / max(len)``. The string edit
    distance of pre-order traversals is a known lower bound of the tree edit distance (every
    tree edit script is also a valid edit script of the pre-order sequence), so this
    approximation can only overestimate similarity, never underestimate it.

    The result is clamped to [0, 1] because a tree edit distance can exceed the size of the
    larger tree.
    """
    size_a = a.size()
    size_b = b.size()
    if size_a <= node_cap and size_b <= node_cap:
        distance = zhang_shasha(a, b)
        method = "zhang-shasha"
    else:
        label_ids: dict[str, int] = {}
        distance = levenshtein(_preorder_labels(a, label_ids), _preorder_labels(b, label_ids))
        method = "preorder-sequence-approximation"
    # Pre-order sequences have exactly one item per node, so max(size) is also max(len).
    similarity = 1.0 - distance / max(size_a, size_b)
    return min(1.0, max(0.0, similarity)), method


def subtree_bag_similarity(a: Node, b: Node) -> float:
    """Multiset Jaccard index of the subtree hashes: sum of min counts / sum of max counts."""
    bag_a = subtree_hashes(a)
    bag_b = subtree_hashes(b)
    total = sum((bag_a | bag_b).values())  # Counter `|` keeps the maximum count of each hash
    if total == 0:
        return 0.0
    return sum((bag_a & bag_b).values()) / total  # Counter `&` keeps the minimum count


def structural_similarity(a: Node, b: Node, node_cap: int = 200) -> dict:
    """Structural similarity of two skeletons after putting their top level in canonical order.

    ``structure`` is the equal-weight mean of the tree-edit-distance similarity (global shape)
    and the subtree-bag similarity (shared building blocks).
    """
    ordered_a = canonical_order(a)
    ordered_b = canonical_order(b)
    ted, method = ted_similarity(ordered_a, ordered_b, node_cap)
    subtree = subtree_bag_similarity(ordered_a, ordered_b)
    return {
        "structure": 0.5 * ted + 0.5 * subtree,
        "ted": ted,
        "subtree": subtree,
        "method": method,
        "a_nodes": a.size(),
        "b_nodes": b.size(),
    }
