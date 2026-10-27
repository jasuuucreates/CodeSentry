"""Structural skeleton of a C program, built with the tree-sitter C grammar.

tree-sitter produces a concrete syntax tree: it keeps every parenthesis, semicolon and keyword.
The skeleton keeps only named nodes (real language constructs), translates their types into the
shared vocabulary of :mod:`engine.structure_common`, and leaves out what a copier can change
without changing the program: comments, preprocessor directives, identifier names, literal
values, redundant parentheses and function prototypes.

tree-sitter never refuses to parse; on invalid code it inserts ``ERROR`` and missing nodes and
carries on. :func:`c_skeleton` therefore always returns a tree and reports problems through the
``last_had_errors`` flag, which the pipeline turns into a warning.
"""
from __future__ import annotations

import tree_sitter_c
from tree_sitter import Language, Parser

from .models import Node
from .structure_common import OPERATOR_LABELS, UNARY_OPERATOR_LABELS, canonical_label

# Loading the compiled grammar is the expensive part, so the parser is built once per process.
_PARSER = Parser(Language(tree_sitter_c.language()))

_COMPARISON_OPERATORS = frozenset({"==", "!=", "<", ">", "<=", ">="})
_BOOLEAN_OPERATORS = frozenset({"&&", "||"})

# Literals and type names become leaves: what is inside them (the digits of a number, the
# characters of a string, the spelling of a type) is exactly what the skeleton ignores.
_LEAF_TYPES = frozenset({
    "number_literal", "string_literal", "char_literal", "concatenated_string",
    "true", "false", "null",
    "primitive_type", "type_identifier", "sized_type_specifier", "type_descriptor",
})

# `struct`, `union` and `enum` either define a type (they have a body) or merely name one.
_TYPE_SPECIFIERS = frozenset({"struct_specifier", "union_specifier", "enum_specifier"})

# Expressions that Python writes as statements of their own.
_ASSIGNMENT_TYPES = frozenset({"assignment_expression", "update_expression"})

# True when the most recent c_skeleton() call met a syntax error. Also available as
# `c_skeleton.last_had_errors`, the name the architecture contract uses.
last_had_errors = False


def _operator_text(ts_node) -> str:
    """Operator of an expression node, e.g. ``'+='``; tree-sitter uses the operator as its type."""
    operator = ts_node.child_by_field_name("operator")
    return operator.type if operator is not None else ""


def _is_prototype(declaration) -> bool:
    """True for a function prototype such as ``int add(int a, int b);``.

    A prototype only exists because a C compiler reads the file top to bottom; it adds no
    behaviour. Dropping prototypes means that reordering functions (which forces prototypes to be
    added) does not change the skeleton. Function-pointer variables such as ``int (*fp)(int);``
    are real variables and are not treated as prototypes.
    """
    declarators = declaration.children_by_field_name("declarator")
    if not declarators:
        return False
    for declarator in declarators:
        # `int *make(void);` wraps the function declarator in a pointer declarator.
        while declarator.type == "pointer_declarator":
            inner = declarator.child_by_field_name("declarator")
            if inner is None:
                return False
            declarator = inner
        if declarator.type != "function_declarator":
            return False
        name = declarator.child_by_field_name("declarator")
        if name is None or name.type != "identifier":
            return False
    return True


def _expand(ts_node) -> tuple[str | None, list]:
    """Decide the canonical label of one tree-sitter node and what goes beneath it.

    Returns ``(label, entries)``. A `label` of None drops the node itself and its `entries` are
    attached to its parent instead. Each entry is either a tree-sitter node still to be visited
    or a ready-made skeleton leaf (an operator such as ``Add``).
    """
    kind = ts_node.type
    if kind in _LEAF_TYPES:
        return canonical_label("c", kind), []
    if kind == "declaration" and _is_prototype(ts_node):
        return None, []
    if kind in _TYPE_SPECIFIERS and ts_node.child_by_field_name("body") is None:
        return "Type", []
    if kind == "update_expression":
        # `i++` means `i += 1`, so it gets exactly the skeleton of `i += 1`, whether the operator
        # is written before or after the variable.
        step = "Add" if _operator_text(ts_node) == "++" else "Sub"
        argument = ts_node.child_by_field_name("argument")
        target = [argument] if argument is not None and not argument.is_missing else []
        return "AugAssign", target + [Node(step), Node("Const")]

    label = canonical_label("c", kind)
    operator_leaf = None
    if kind == "binary_expression":
        operator = _operator_text(ts_node)
        if operator in _COMPARISON_OPERATORS:
            label = "Compare"
        elif operator in _BOOLEAN_OPERATORS:
            label = "BoolOp"
        operator_leaf = OPERATOR_LABELS.get(operator)
    elif kind == "unary_expression":
        operator_leaf = UNARY_OPERATOR_LABELS.get(_operator_text(ts_node))
    elif kind == "assignment_expression":
        operator = _operator_text(ts_node)
        if operator != "=":
            # `total += x` -> AugAssign[Var, Add, Var], the same shape Python's ast gives it.
            label = "AugAssign"
            operator_leaf = OPERATOR_LABELS.get(operator[:-1])
    elif kind == "expression_statement":
        named = [child for child in ts_node.named_children if not child.is_missing]
        if not named:
            return "Pass", []  # a lone `;` is C's equivalent of Python's `pass`
        if len(named) == 1 and named[0].type in _ASSIGNMENT_TYPES:
            # In Python an assignment is a statement by itself, not an expression statement.
            label = None

    preprocessor = kind.startswith("preproc_")
    # The one field whose child is left out: a function's own name, or the name of a struct.
    # Python keeps those names as strings, not nodes, so dropping them keeps the two alike.
    if kind == "function_declarator":
        dropped_field = "declarator"
    elif kind in _TYPE_SPECIFIERS:
        dropped_field = "name"
    else:
        dropped_field = None

    entries: list = []
    for index, child in enumerate(ts_node.children):
        if child.is_missing:
            continue  # inserted by error recovery; it does not exist in the source text
        if not child.is_named:
            if operator_leaf is not None and ts_node.field_name_for_child(index) == "operator":
                entries.append(Node(operator_leaf))
            continue
        if preprocessor:
            # A directive's name, condition, path or replacement text is not program logic,
            # but the code guarded by `#if`/`#ifdef` (children outside any field, and the
            # `alternative` branch) is.
            if ts_node.field_name_for_child(index) not in (None, "alternative"):
                continue
        elif dropped_field is not None and ts_node.field_name_for_child(index) == dropped_field:
            # Only a plain name is dropped; `(*fp)(int)` declares a real pointer variable.
            if kind != "function_declarator" or child.type == "identifier":
                continue
        entries.append(child)
    return label, entries


def c_skeleton(text: str) -> Node:
    """Parse C source with tree-sitter and return its canonical skeleton (root ``Program``).

    Never raises on invalid code. If the parse tree contains ``ERROR`` or missing nodes, the tree
    is still returned and ``c_skeleton.last_had_errors`` (and the module-level
    ``last_had_errors``) is set to True; otherwise both are reset to False.

    The walk uses an explicit stack, so deeply nested code cannot exceed the recursion limit.
    Entries are pushed in reverse and popped in source order, and each subtree is finished before
    its next sibling is popped, which keeps children in source order even when dropped nodes
    promote their children to the parent.
    """
    global last_had_errors
    root = _PARSER.parse(text.encode("utf-8", errors="replace")).root_node
    had_errors = root.has_error
    last_had_errors = had_errors
    c_skeleton.last_had_errors = had_errors

    holder: list[Node] = []
    stack: list = [(root, holder)]
    while stack:
        entry, siblings = stack.pop()
        if isinstance(entry, Node):
            siblings.append(entry)
            continue
        label, entries = _expand(entry)
        if label is None:
            target = siblings
        else:
            node = Node(label)
            siblings.append(node)
            target = node.children
        stack.extend((item, target) for item in reversed(entries))
    return holder[0]


c_skeleton.last_had_errors = False
