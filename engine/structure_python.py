"""Structural skeleton of a Python program, built with the standard ``ast`` module.

The skeleton is the abstract syntax tree with every node type translated into the canonical
vocabulary of :mod:`engine.structure_common`. Names and literal values are not nodes of the
``ast`` tree at all (they are plain strings and numbers stored on the nodes), so they never reach
the skeleton; renaming every variable therefore leaves the skeleton unchanged.
"""
from __future__ import annotations

import ast

from .models import Node, StructureError
from .structure_common import canonical_label

# Node types whose body may start with a docstring. A docstring is documentation, not logic,
# so adding, removing or rewording one must not change the skeleton.
_DOCSTRING_OWNERS = (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)

# List fields that hold an alternative block of statements. ``ast`` stores them as plain lists
# next to the main body (``If.body`` and ``If.orelse``), so without a wrapper node the statements
# of the else branch would be indistinguishable from those of the if branch. Wrapping `orelse`
# in ``Else`` also matches C, where tree-sitter has an explicit ``else_clause``.
_WRAPPED_FIELDS = {"orelse": "Else", "finalbody": "Finally"}


def _is_docstring(statement: ast.AST) -> bool:
    """True when `statement` is a bare string literal used as a docstring."""
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _child_entries(node: ast.AST) -> list:
    """The children of `node` in source (field) order.

    Each entry is either an ``ast`` node or a ``(label, [ast nodes])`` group, which becomes a
    wrapper node such as ``Else`` holding that list of statements.
    """
    entries: list = []
    for name, value in ast.iter_fields(node):
        if isinstance(value, ast.AST):
            entries.append(value)
        elif isinstance(value, list):
            # Lists can contain None placeholders (e.g. `Dict.keys` for `**mapping`).
            items = [item for item in value if isinstance(item, ast.AST)]
            if name == "body" and isinstance(node, _DOCSTRING_OWNERS) and items and _is_docstring(items[0]):
                items = items[1:]
            if not items:
                continue
            if name in _WRAPPED_FIELDS:
                entries.append((_WRAPPED_FIELDS[name], items))
            else:
                entries.extend(items)
    return entries


def python_skeleton(text: str) -> Node:
    """Parse Python source and return its canonical skeleton (root label ``Program``).

    Raises :class:`StructureError` when the source is not valid Python.

    The tree is walked with an explicit stack instead of recursion, so deeply nested code
    cannot hit Python's recursion limit. Entries are pushed in reverse so they are popped in
    source order, and a node's whole subtree is finished before its next sibling is popped;
    that keeps every children list in source order, even when a dropped node (such as an
    expression context) hands its children to its parent.
    """
    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        raise StructureError(f"Python syntax error on line {exc.lineno}: {exc.msg}") from None
    except (ValueError, RecursionError, MemoryError) as exc:
        # ValueError: e.g. null bytes in the source; RecursionError/MemoryError: nesting so deep
        # that CPython's own parser gives up.
        raise StructureError(f"Python source could not be parsed: {exc}") from None

    holder: list[Node] = []
    stack: list = [(tree, holder)]
    while stack:
        entry, siblings = stack.pop()
        if isinstance(entry, tuple):
            label, items = entry
            group = Node(label)
            siblings.append(group)
            stack.extend((item, group.children) for item in reversed(items))
            continue

        label = canonical_label("python", type(entry).__name__)
        if label is None:
            target = siblings
        else:
            node = Node(label)
            siblings.append(node)
            target = node.children
        stack.extend((child, target) for child in reversed(_child_entries(entry)))
    return holder[0]
