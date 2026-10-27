"""Shared vocabulary of the structural (syntax-tree) stage.

Python's ``ast`` module and tree-sitter's C grammar name their nodes very differently
(``For`` versus ``for_statement``, ``Name`` versus ``identifier``). Before two programs can be
compared structurally, every raw node type is translated into one small canonical vocabulary
(``Loop``, ``Var``, ``Call`` ...). The translation deliberately forgets everything a plagiarist
can change cheaply -- identifier names, literal values, the kind of loop -- and keeps the shape
of the program. See docs/ARCHITECTURE_CONTRACT.md, section 5.
"""
from __future__ import annotations

from .models import EngineError

# C operator text -> the name Python's ``ast`` module uses for the same operator, so that both
# languages produce identical operator leaves (``a + b`` is ``BinOp[Var, Add, Var]`` in both).
OPERATOR_LABELS: dict[str, str] = {
    "+": "Add", "-": "Sub", "*": "Mult", "/": "Div", "%": "Mod",
    "<": "Lt", ">": "Gt", "<=": "LtE", ">=": "GtE", "==": "Eq", "!=": "NotEq",
    "&&": "And", "||": "Or",
    "&": "BitAnd", "|": "BitOr", "^": "BitXor", "<<": "LShift", ">>": "RShift",
}

# C prefix operators of ``unary_expression`` -> Python ``ast`` unary operator names.
UNARY_OPERATOR_LABELS: dict[str, str] = {"-": "USub", "+": "UAdd", "!": "Not", "~": "Invert"}

# Python ``ast`` class name -> canonical label. A value of None means "drop this node and hand
# its children to the parent". Operator classes (Add, Lt, USub ...) already carry the canonical
# names, so they fall through to the default rule unchanged.
_PYTHON_LABELS: dict[str, str | None] = {
    "Module": "Program",
    "FunctionDef": "Function", "AsyncFunctionDef": "Function", "Lambda": "Function",
    "ClassDef": "Class",
    "arguments": "Params", "arg": "Param",
    "Return": "Return",
    "Assign": "Assign", "AnnAssign": "Assign", "NamedExpr": "Assign",
    "AugAssign": "AugAssign",
    # Every loop form is a Loop: rewriting a for loop as a while loop keeps the skeleton.
    "For": "Loop", "AsyncFor": "Loop", "While": "Loop",
    "If": "If", "IfExp": "If",
    "Match": "Switch", "match_case": "Case",
    "Try": "Try", "TryStar": "Try",
    "With": "With", "AsyncWith": "With",
    "Break": "Break", "Continue": "Continue", "Pass": "Pass",
    "Call": "Call",
    "BinOp": "BinOp", "BoolOp": "BoolOp", "UnaryOp": "UnaryOp", "Compare": "Compare",
    "Subscript": "Index", "Attribute": "Attr",
    "Name": "Var", "Constant": "Const",
    "List": "Collection", "Tuple": "Collection", "Set": "Collection",
    "Dict": "Dict",
    "ListComp": "Comprehension", "SetComp": "Comprehension",
    "DictComp": "Comprehension", "GeneratorExp": "Comprehension",
    "Expr": "ExprStmt",
    "Import": "Import", "ImportFrom": "Import",
    "Global": "Decl", "Nonlocal": "Decl",
    # Expression contexts only say whether a name is read or written; the position of the
    # name in the tree already tells us that.
    "Load": None, "Store": None, "Del": None,
    # Pure grouping nodes: their children are what matters.
    "withitem": None, "comprehension": None, "alias": None,
}

# tree-sitter C node type -> canonical label (None = drop and promote the children).
_C_LABELS: dict[str, str | None] = {
    "translation_unit": "Program",
    "function_definition": "Function",
    "struct_specifier": "Class", "union_specifier": "Class",
    "parameter_list": "Params", "parameter_declaration": "Param",
    "return_statement": "Return",
    "assignment_expression": "Assign", "init_declarator": "Assign",
    "update_expression": "AugAssign",
    "for_statement": "Loop", "while_statement": "Loop", "do_statement": "Loop",
    "if_statement": "If", "conditional_expression": "If",
    "else_clause": "Else",
    "switch_statement": "Switch", "case_statement": "Case",
    "break_statement": "Break", "continue_statement": "Continue",
    "call_expression": "Call",
    "binary_expression": "BinOp", "unary_expression": "UnaryOp",
    "subscript_expression": "Index", "field_expression": "Attr",
    "identifier": "Var",
    "number_literal": "Const", "string_literal": "Const", "char_literal": "Const",
    "concatenated_string": "Const", "true": "Const", "false": "Const", "null": "Const",
    "initializer_list": "Collection",
    "expression_statement": "ExprStmt",
    "declaration": "Decl", "field_declaration": "Decl",
    "compound_statement": "Block",
    "primitive_type": "Type", "type_identifier": "Type", "sized_type_specifier": "Type",
    "type_descriptor": "Type",
    "pointer_declarator": "Ptr", "abstract_pointer_declarator": "Ptr",
    "array_declarator": "Array", "abstract_array_declarator": "Array",
    # Formatting and grouping nodes: parentheses, argument brackets, braces of a struct body.
    "comment": None,
    "parenthesized_expression": None, "argument_list": None,
    "function_declarator": None, "abstract_function_declarator": None,
    "field_declaration_list": None, "enumerator_list": None,
    # Modifiers such as `static` or `const` do not change the shape of the algorithm.
    "storage_class_specifier": None, "type_qualifier": None,
    # Names of struct fields and goto labels are identifiers, which the skeleton never keeps.
    "field_identifier": None, "statement_identifier": None,
}


def _camel_case(raw: str) -> str:
    """Derive a readable label from a raw type name: ``goto_statement`` -> ``GotoStatement``.

    Only the first letter of each underscore-separated part is upper-cased, so names that are
    already CamelCase (``JoinedStr``) stay exactly as they are.
    """
    return "".join(part[:1].upper() + part[1:] for part in raw.split("_") if part)


def canonical_label(language: str, raw: str) -> str | None:
    """Map a raw syntax-tree node type to its canonical label, or None to drop the node.

    A dropped node disappears from the skeleton and its children are attached to its parent.
    Node types that have no explicit mapping keep a label derived from their own name, so no
    information is silently thrown away for constructs the table does not know about.
    """
    if language == "python":
        table = _PYTHON_LABELS
    elif language == "c":
        if raw.startswith("preproc_"):
            return None
        table = _C_LABELS
    else:
        raise EngineError(f"unsupported language: {language!r}")
    if raw in table:
        return table[raw]
    return _camel_case(raw)
