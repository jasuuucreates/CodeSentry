"""Plagiarism obfuscator: makes disguised copies of a program for the evaluation dataset.

Think of a student who copies a friend's assignment and then tries to hide it. They do not write
anything new; they only change the surface: give the variables new names, delete the friend's
comments and write their own, shuffle the order of the functions, turn a ``for`` loop into a
``while`` loop, sprinkle in a few lines that do nothing. The program still does exactly the same
thing. This module performs exactly those disguises, automatically and repeatably, so the
detector can be tested against them.

The same ideas with their proper names (docs/ARCHITECTURE_CONTRACT.md, section 9):

* ``rename``          - consistent identifier renaming (functions except ``main``, parameters,
                        local and global variables). Builtins, library functions, imported names,
                        attributes, struct fields, dunder names and keywords are never renamed.
* ``comments_format`` - comments removed and different ones written; blank-line layout changed;
                        Python re-indented from 4 to 2 spaces, C brace style switched
                        (K&R <-> Allman).
* ``reorder``         - top-level function definitions shuffled (C: prototypes inserted so the
                        file stays valid).
* ``loop_swap``       - counted ``for`` loops without ``continue`` become equivalent ``while``
                        loops.
* ``dead_code``       - 3 to 6 unused variables plus one never-called helper function.
* ``combined``        - rename -> loop_swap -> reorder -> dead_code -> comments_format.

Python transforms work on the ``ast`` and print it back with ``ast.unparse``. C transforms use
tree-sitter only to *locate* nodes and then apply careful text edits, so the rest of the file is
left byte-for-byte untouched. Every result is checked to be syntactically valid (Python:
``ast.parse``; C: tree-sitter with no ERROR or missing node) and different from the input,
otherwise ``ValueError`` is raised. All randomness comes from ``random.Random(seed)``, so a
given seed always produces the same output.
"""
from __future__ import annotations

import ast
import builtins
import keyword
import random
import re

OBFUSCATION_TYPES = ("rename", "comments_format", "reorder", "loop_swap", "dead_code", "combined")

# ---------------------------------------------------------------------------------------------
# Shared: plausible new names
# ---------------------------------------------------------------------------------------------

# Word-level synonyms: a renamed identifier keeps looking like something a student would write.
_SYNONYMS = {
    "calculate": ["compute", "work_out", "determine"], "compute": ["calculate", "evaluate", "derive"],
    "find": ["locate", "search", "get"], "get": ["fetch", "obtain", "read"],
    "check": ["verify", "test", "validate"], "is": ["check", "has"], "print": ["show", "display", "output"],
    "show": ["display", "print", "report"], "display": ["show", "render"], "make": ["build", "create"],
    "build": ["make", "construct"], "add": ["append", "insert", "put"], "remove": ["delete", "drop"],
    "update": ["refresh", "modify"], "convert": ["transform", "translate"], "apply": ["use", "perform"],
    "count": ["tally", "num", "amount"], "counts": ["tallies", "freq"], "total": ["running_sum", "acc", "grand"],
    "sum": ["accumulated", "acc_total"], "mean": ["average", "avg"], "average": ["mean_value", "avg"],
    "avg": ["average", "mean_val"], "median": ["middle_value", "mid_val"], "std": ["spread", "sigma"],
    "dev": ["deviation", "spread"], "marks": ["scores", "points", "results"], "mark": ["score", "point"],
    "score": ["mark", "points"], "scores": ["marks", "points"], "students": ["pupils", "learners"],
    "student": ["pupil", "learner"], "name": ["label", "title"], "names": ["labels", "titles"],
    "grade": ["band", "level"], "grades": ["bands", "levels"], "list": ["seq", "items"],
    "number": ["value", "num"], "num": ["number", "val"], "numbers": ["values", "nums"],
    "index": ["pos", "position"], "idx": ["pos", "index"], "value": ["val", "item"],
    "values": ["vals", "items"], "result": ["outcome", "answer"], "results": ["outcomes", "answers"],
    "matrix": ["grid", "table"], "row": ["line", "r_idx"], "rows": ["lines", "height"],
    "col": ["column", "c_idx"], "cols": ["columns", "width"], "size": ["length", "dim"],
    "len": ["length", "size"], "length": ["size", "len_value"], "temp": ["tmp", "swap_val"],
    "tmp": ["temp", "hold"], "prime": ["prm", "primal"], "primes": ["prime_list", "prms"],
    "limit": ["bound", "upper"], "max": ["largest", "highest"], "min": ["smallest", "lowest"],
    "best": ["top", "leader"], "high": ["upper", "hi"], "low": ["lower", "lo"], "mid": ["middle", "centre"],
    "left": ["lo_idx", "start"], "right": ["hi_idx", "end"], "start": ["begin", "first"],
    "end": ["stop", "last"], "first": ["initial", "head"], "last": ["final", "tail"],
    "word": ["token", "term"], "words": ["tokens", "terms"], "text": ["sentence", "content"],
    "string": ["text", "str_value"], "char": ["symbol", "letter"], "ch": ["symbol", "letter"],
    "vowels": ["vowel_count", "nv"], "consonants": ["consonant_count", "nc"], "freq": ["frequency", "counts"],
    "frequency": ["freq", "occurrences"], "reverse": ["flip", "invert"], "reversed": ["flipped", "inverted"],
    "palindrome": ["mirror", "symmetric"], "account": ["acct", "wallet"], "accounts": ["accts", "wallets"],
    "balance": ["funds", "amount_left"], "amount": ["sum_value", "money"], "deposit": ["credit", "put_in"],
    "withdraw": ["debit", "take_out"], "interest": ["growth", "yield_amt"], "rate": ["pct", "ratio"],
    "log": ["history", "journal"], "transaction": ["entry", "txn"], "transactions": ["entries", "txns"],
    "array": ["arr", "data"], "arr": ["array", "data"], "data": ["items", "dataset"], "items": ["elements", "entries"],
    "item": ["element", "entry"], "key": ["target", "needle"], "target": ["key", "wanted"],
    "sort": ["order", "arrange"], "sorted": ["ordered", "arranged"], "search": ["lookup", "seek"],
    "binary": ["bin", "base2"], "comparisons": ["compares", "steps"], "swap": ["exchange", "switch"],
    "stack": ["pile", "stk"], "top": ["peak", "head"], "push": ["put", "stack_add"], "pop": ["take", "stack_remove"],
    "bracket": ["brace", "paren"], "brackets": ["braces", "parens"], "open": ["opening", "left_sym"],
    "close": ["closing", "right_sym"], "balanced": ["matched", "ok"], "expr": ["expression", "formula"],
    "expression": ["expr", "formula"], "base": ["radix", "system"], "digit": ["figure", "numeral"],
    "digits": ["figures", "numerals"], "decimal": ["dec", "base10"], "octal": ["oct", "base8"],
    "hex": ["hexa", "base16"], "hexadecimal": ["base16", "hexa"], "remainder": ["rem", "leftover"],
    "quotient": ["quot", "ratio"], "inventory": ["stock", "catalogue"], "price": ["cost", "rate_each"],
    "quantity": ["qty", "units"], "qty": ["quantity", "units"], "discount": ["rebate", "reduction"],
    "gst": ["tax", "levy"], "tax": ["levy", "duty"], "bill": ["invoice", "receipt"], "subtotal": ["sub_sum", "partial"],
    "readings": ["samples", "measurements"], "reading": ["sample", "measurement"], "temps": ["temperatures", "samples"],
    "temperature": ["temp_value", "degrees"], "temperatures": ["degree_list", "samples"], "day": ["date_idx", "day_no"],
    "days": ["day_list", "n_days"], "window": ["span", "frame"], "moving": ["rolling", "sliding"],
    "streak": ["run", "sequence"], "rising": ["increasing", "climbing"], "current": ["cur", "now"],
    "cur": ["current", "present"], "prev": ["previous", "before"], "previous": ["prev", "earlier"],
    "next": ["following", "after"], "flag": ["marker", "signal"], "found": ["located", "hit"],
    "i": ["idx", "pos"], "j": ["jdx", "inner"], "k": ["kdx", "step_no"], "n": ["size", "count_n"],
    "m": ["width", "cols_n"], "x": ["val", "num_x"], "y": ["other", "num_y"], "a": ["first_val", "lhs"],
    "b": ["second_val", "rhs"], "c": ["ch_val", "third_val"], "s": ["text_s", "line_s"], "t": ["tmp_t", "hold_t"],
    "v": ["item_v", "elem"], "p": ["ptr", "cursor"], "q": ["quo", "q_val"], "d": ["divisor", "d_val"],
    "r": ["rem_val", "r_val"], "w": ["word_w", "width_w"], "e": ["elem_e", "entry_e"], "z": ["z_val", "last_z"],
    "main": ["main"], "matrices": ["grids", "tables"], "determinant": ["det", "det_value"], "det": ["determinant", "det_val"],
    "transpose": ["flip_axes", "transposed"], "multiply": ["product_of", "times"], "product": ["prod", "mult_result"],
    "twin": ["paired", "twins"], "sieve": ["filter_table", "marks_table"], "is_prime": ["prime_check", "check_prime"],
}

_PREFIXES = ["my_", "the_", "cur_", "local_", "tmp_"]
_SUFFIXES = ["_val", "_data", "_info", "_value", "_item"]


def _split_words(name: str) -> list[str]:
    parts = [p for p in name.split("_") if p]
    words: list[str] = []
    for part in parts:
        # also split camelCase
        words.extend(w.lower() for w in re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?![a-z])", part) or [part])
    return words


def _candidate_names(name: str, rng: random.Random) -> list[str]:
    """Plausible replacement names for `name`, best first."""
    words = _split_words(name)
    upper = name.isupper() and len(name) > 1
    candidates: list[str] = []
    if words:
        swapped = []
        changed = False
        for word in words:
            options = _SYNONYMS.get(word)
            if options:
                swapped.append(rng.choice(options))
                changed = True
            else:
                swapped.append(word)
        if changed:
            deduped = [w for i, w in enumerate(swapped) if i == 0 or w != swapped[i - 1]]
            candidates.append("_".join(deduped))
        # every alternative synonym combination for the first replaceable word
        for i, word in enumerate(words):
            for option in _SYNONYMS.get(word, []):
                alt = words[:i] + [option] + words[i + 1:]
                candidates.append("_".join(alt))
    base = "_".join(words) if words else name.lower()
    prefix = rng.choice(_PREFIXES)
    suffix = rng.choice(_SUFFIXES)
    candidates.extend([prefix + base, base + suffix, base + "_2"])
    if upper:
        candidates = [c.upper() for c in candidates]
    return candidates


def _build_mapping(names: list[str], taken: set[str], rng: random.Random) -> dict[str, str]:
    """Map every name to a new plausible name that collides with nothing in `taken`."""
    mapping: dict[str, str] = {}
    used = set(taken)
    for name in names:
        new = None
        for candidate in _candidate_names(name, rng):
            if (candidate != name and candidate.isidentifier() and not keyword.iskeyword(candidate)
                    and candidate not in used):
                new = candidate
                break
        counter = 2
        while new is None:
            candidate = f"{name}_v{counter}"
            if candidate not in used:
                new = candidate
            counter += 1
        mapping[name] = new
        used.add(new)
    return mapping


# Comment phrases written by the "copying student" (deliberately generic).
_COMMENT_PHRASES = [
    "helper routine", "main logic of this part", "does the actual work here", "utility function",
    "step of the assignment", "core computation", "small helper used below", "processing routine",
    "compute and return the answer", "handles one task of the program",
]
_HEADER_PHRASES = [
    "Lab assignment solution", "Programming assignment - my submission", "Assignment program",
    "Solution file for the lab exercise", "Course assignment code",
]


# ---------------------------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------------------------

_C_PARSER = None


def _c_parser():
    global _C_PARSER
    if _C_PARSER is None:
        import tree_sitter_c
        from tree_sitter import Language, Parser
        _C_PARSER = Parser(Language(tree_sitter_c.language()))
    return _C_PARSER


def _c_parse(src: bytes):
    return _c_parser().parse(src)


def c_tree_has_errors(tree) -> bool:
    """True if a tree-sitter tree contains any ERROR or missing node."""
    stack = [tree.root_node]
    while stack:
        node = stack.pop()
        if node.type == "ERROR" or node.is_missing or node.is_error:
            return True
        stack.extend(node.children)
    return False


def is_valid(text: str, language: str) -> bool:
    """Python: ``ast.parse`` succeeds. C: tree-sitter finds no ERROR or missing node."""
    if language == "python":
        try:
            ast.parse(text)
        except SyntaxError:
            return False
        return True
    if language == "c":
        return not c_tree_has_errors(_c_parse(text.encode("utf-8")))
    raise ValueError(f"unsupported language {language!r}")


def _check_result(original: str, new: str, language: str, kind: str) -> None:
    if not is_valid(new, language):
        raise ValueError(f"{kind}: transformed {language} code is not syntactically valid")
    if new == original:
        raise ValueError(f"{kind}: transformation produced no change")


# ---------------------------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------------------------

def obfuscate(text: str, language: str, kind: str, seed: int = 0) -> tuple[str, dict]:
    """Return ``(new_text, report)``; report = ``{"kind", "changes", "details"}``.

    Raises ValueError for an unknown kind/language, invalid input, or when the transformation
    cannot produce a valid, different program.
    """
    if kind not in OBFUSCATION_TYPES:
        raise ValueError(f"unknown obfuscation kind {kind!r}; expected one of {OBFUSCATION_TYPES}")
    if language not in ("python", "c"):
        raise ValueError(f"unsupported language {language!r}")
    if not is_valid(text, language):
        raise ValueError(f"input {language} code is not syntactically valid")

    if kind == "combined":
        current = text
        details: list[str] = []
        changes = 0
        for offset, step in enumerate(("rename", "loop_swap", "reorder", "dead_code", "comments_format")):
            try:
                current, report = _single(current, language, step, seed + offset)
            except ValueError as exc:
                details.append(f"{step}: skipped ({exc})")
                continue
            changes += report["changes"]
            details.append(f"{step}: {report['changes']} change(s)")
            details.extend(f"  {d}" for d in report["details"])
        _check_result(text, current, language, kind)
        return current, {"kind": kind, "changes": changes, "details": details}

    new, report = _single(text, language, kind, seed)
    return new, report


def _single(text: str, language: str, kind: str, seed: int) -> tuple[str, dict]:
    rng = random.Random(f"{kind}:{seed}")
    func = _PY_TRANSFORMS[kind] if language == "python" else _C_TRANSFORMS[kind]
    new, changes, details = func(text, rng)
    _check_result(text, new, language, kind)
    if changes <= 0:
        raise ValueError(f"{kind}: nothing to change")
    return new, {"kind": kind, "changes": changes, "details": details}


# =============================================================================================
# Python transforms
# =============================================================================================

_PY_BUILTINS = set(dir(builtins))


def _py_all_identifiers(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
            names.add(node.name.split(".")[0])
        elif isinstance(node, ast.keyword) and node.arg:
            names.add(node.arg)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            names.update(node.names)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            names.add(node.name)
    return names


def _py_strip_docstrings(tree: ast.Module) -> int:
    removed = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                    and isinstance(body[0].value.value, str):
                body.pop(0)
                removed += 1
                if not body:
                    body.append(ast.Pass())
    return removed


def _py_body_start(body: list[ast.stmt]) -> int:
    """Index after a leading docstring (if any)."""
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        return 1
    return 0


# ---- rename ----------------------------------------------------------------------------------

def _py_rename(text: str, rng: random.Random):
    tree = ast.parse(text)
    protected: set[str] = {"self", "cls", "main", "_"} | _PY_BUILTINS | set(keyword.kwlist)
    for node in ast.walk(tree):
        if isinstance(node, ast.alias):
            protected.add((node.asname or node.name).split(".")[0])
            protected.add(node.name.split(".")[0])
        elif isinstance(node, ast.keyword) and node.arg:
            protected.add(node.arg)          # keyword arguments must keep matching parameter names
        elif isinstance(node, ast.ClassDef):
            protected.add(node.name)
            for stmt in node.body:          # class attributes and methods are reached via attributes
                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    protected.add(stmt.name)
                for sub in ast.walk(stmt) if not isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)) else []:
                    if isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Store):
                        protected.add(sub.id)
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) \
                and node.func.id in {"globals", "locals", "vars", "eval", "exec", "getattr", "setattr"}:
            for arg in node.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    protected.add(arg.value)

    candidates: list[str] = []

    def want(name: str) -> None:
        if name in protected or (name.startswith("__") and name.endswith("__")):
            return
        if name not in candidates:
            candidates.append(name)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            want(node.name)
        elif isinstance(node, ast.arg):
            want(node.arg)
        elif isinstance(node, ast.Name) and isinstance(node.ctx, (ast.Store, ast.Del)):
            want(node.id)
        elif isinstance(node, ast.ExceptHandler) and node.name:
            want(node.name)
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            for name in node.names:
                want(name)
    # keep definition order deterministic
    if not candidates:
        return text, 0, []
    mapping = _build_mapping(candidates, _py_all_identifiers(tree) | protected, rng)

    class Renamer(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id in mapping:
                node.id = mapping[node.id]
            return node

        def visit_arg(self, node):
            if node.arg in mapping:
                node.arg = mapping[node.arg]
            self.generic_visit(node)
            return node

        def _visit_def(self, node):
            if node.name in mapping:
                node.name = mapping[node.name]
            self.generic_visit(node)
            return node

        visit_FunctionDef = _visit_def
        visit_AsyncFunctionDef = _visit_def

        def visit_ExceptHandler(self, node):
            if node.name in mapping:
                node.name = mapping[node.name]
            self.generic_visit(node)
            return node

        def visit_Global(self, node):
            node.names = [mapping.get(n, n) for n in node.names]
            return node

        visit_Nonlocal = visit_Global

    tree = Renamer().visit(tree)
    ast.fix_missing_locations(tree)
    new = ast.unparse(tree) + "\n"
    details = [f"{old} -> {new_name}" for old, new_name in mapping.items()]
    return new, len(mapping), details


# ---- comments_format ---------------------------------------------------------------------------

def _py_comments_format(text: str, rng: random.Random):
    tree = ast.parse(text)
    old_comments = sum(1 for line in text.splitlines() if line.strip().startswith("#")) + \
        len(re.findall(r"[^\s#]\s*#", text))
    removed_docstrings = _py_strip_docstrings(tree)
    ast.fix_missing_locations(tree)
    reference = ast.dump(tree)
    plain = ast.unparse(tree)

    def_blank = rng.choice([0, 2, 3])
    lines_out: list[str] = []
    added = 0
    header = rng.choice(_HEADER_PHRASES)
    lines_out.append(f"# {header}")
    lines_out.append("# (reformatted)")
    added += 2
    for line in plain.splitlines():
        if not line.strip():
            continue                                    # drop the original blank-line layout
        stripped = line.lstrip(" ")
        depth_spaces = len(line) - len(stripped)
        indent = " " * (depth_spaces // 2)              # 4-space indentation becomes 2-space
        if stripped.startswith(("def ", "async def ", "class ")):
            if depth_spaces == 0:
                lines_out.extend([""] * def_blank)
            name = re.match(r"(?:async\s+)?(?:def|class)\s+(\w+)", stripped).group(1)
            phrase = rng.choice(_COMMENT_PHRASES)
            lines_out.append(f"{indent}# {name.replace('_', ' ')}: {phrase}")
            added += 1
        elif stripped.startswith(("for ", "while ")) and rng.random() < 0.5:
            lines_out.append(f"{indent}# loop over the values")
            added += 1
        elif stripped.startswith("return ") and depth_spaces > 0 and lines_out \
                and not lines_out[-1].rstrip().endswith(":"):
            lines_out.append("")                        # blank line before a return
        elif stripped.startswith("if __name__"):
            lines_out.extend(["", "", f"# program entry point"])
            added += 1
        lines_out.append(indent + stripped)
    new = "\n".join(lines_out) + "\n"
    try:
        check = ast.dump(ast.parse(new))
    except SyntaxError as exc:
        raise ValueError(f"comments_format: re-indentation broke the code ({exc})") from exc
    if check != reference:
        raise ValueError("comments_format: re-indentation changed the program structure")
    details = [f"removed about {old_comments} comment(s) and {removed_docstrings} docstring(s)",
               f"added {added} new comment(s)", "re-indented 4 -> 2 spaces",
               f"blank lines between top-level definitions: {def_blank}"]
    return new, max(1, old_comments + removed_docstrings + added), details


# ---- reorder -------------------------------------------------------------------------------------

def _py_loads(node: ast.AST, skip_deferred: bool = True) -> set[str]:
    """Names loaded when `node` executes (bodies of nested defs/lambdas are deferred)."""
    names: set[str] = set()
    stack = [node]
    while stack:
        cur = stack.pop()
        if isinstance(cur, ast.Name) and isinstance(cur.ctx, ast.Load):
            names.add(cur.id)
        if skip_deferred and cur is not node and isinstance(cur, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stack.extend(_py_def_time_nodes(cur))
            continue
        if skip_deferred and isinstance(cur, ast.Lambda):
            stack.extend(cur.args.defaults + [d for d in cur.args.kw_defaults if d is not None])
            continue
        stack.extend(ast.iter_child_nodes(cur))
    return names


def _py_def_time_nodes(fn) -> list[ast.AST]:
    nodes: list[ast.AST] = list(fn.decorator_list) + list(fn.args.defaults)
    nodes += [d for d in fn.args.kw_defaults if d is not None]
    for arg in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs + [fn.args.vararg, fn.args.kwarg]:
        if arg is not None and arg.annotation is not None:
            nodes.append(arg.annotation)
    if fn.returns is not None:
        nodes.append(fn.returns)
    return nodes


def _py_bound_names(stmt: ast.stmt) -> set[str]:
    if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        return {stmt.name}
    names = set()
    for node in ast.walk(stmt):
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            names.add(node.id)
        elif isinstance(node, ast.alias):
            names.add((node.asname or node.name).split(".")[0])
    return names


def _py_order_is_safe(body: list[ast.stmt]) -> bool:
    """Static check: no module-level statement needs a module name before it is defined."""
    module_names: set[str] = set()
    functions: dict[str, ast.AST] = {}
    for stmt in body:
        module_names |= _py_bound_names(stmt)
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions[stmt.name] = stmt
    future_annotations = any(isinstance(s, ast.ImportFrom) and s.module == "__future__" and
                             any(a.name == "annotations" for a in s.names) for s in body)

    def closure(names: set[str]) -> set[str]:
        """Names needed when the given names are used at module level (calls run bodies)."""
        needed = set(names)
        frontier = [n for n in names if n in functions]
        seen = set()
        while frontier:
            fname = frontier.pop()
            if fname in seen:
                continue
            seen.add(fname)
            body_loads = _py_loads(ast.Module(body=functions[fname].body, type_ignores=[]), skip_deferred=False)
            needed |= body_loads
            frontier.extend(n for n in body_loads if n in functions)
        return needed

    defined: set[str] = set()
    for stmt in body:
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            nodes = _py_def_time_nodes(stmt)
            if future_annotations:
                nodes = list(stmt.decorator_list) + list(stmt.args.defaults) + \
                    [d for d in stmt.args.kw_defaults if d is not None]
            needed = set()
            for n in nodes:
                needed |= _py_loads(n)
            needed = closure(needed)
        else:
            needed = closure(_py_loads(stmt))
        for name in needed:
            if name in module_names and name not in defined:
                return False
        defined |= _py_bound_names(stmt)
    return True


def _is_main_guard(stmt: ast.stmt) -> bool:
    return (isinstance(stmt, ast.If) and isinstance(stmt.test, ast.Compare)
            and isinstance(stmt.test.left, ast.Name) and stmt.test.left.id == "__name__")


def _py_reorder(text: str, rng: random.Random):
    tree = ast.parse(text)
    body = tree.body
    slots = [i for i, s in enumerate(body) if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if len(slots) < 2:
        return text, 0, []
    funcs = [body[i] for i in slots]
    original_names = [f.name for f in funcs]
    chosen = None
    for _ in range(200):
        order = funcs[:]
        rng.shuffle(order)
        if [f.name for f in order] == original_names:
            continue
        candidate = body[:]
        for slot, fn in zip(slots, order):
            candidate[slot] = fn
        if _py_order_is_safe(candidate):
            chosen = candidate
            break
    if chosen is None:
        # fallback: all functions as one block just before the main guard / at the end
        others = [s for s in body if not isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
        guard = [s for s in others if _is_main_guard(s)]
        others = [s for s in others if not _is_main_guard(s)]
        for _ in range(200):
            order = funcs[:]
            rng.shuffle(order)
            candidate = others + order + guard
            if [s for s in candidate] != body and _py_order_is_safe(candidate):
                chosen = candidate
                break
    if chosen is None:
        raise ValueError("reorder: no safe new order of the functions exists")
    tree.body = chosen
    new = ast.unparse(tree) + "\n"
    new_names = [s.name for s in chosen if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
    moved = sum(1 for a, b in zip(original_names, new_names) if a != b)
    return new, moved, [f"function order: {', '.join(new_names)}"]


# ---- loop_swap -----------------------------------------------------------------------------------

def _py_scope_nodes(scope: ast.AST):
    """Nodes of one scope, not descending into nested function / class / lambda scopes."""
    stack = list(ast.iter_child_nodes(scope))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
            continue
        stack.extend(ast.iter_child_nodes(node))


def _contains_continue(body: list[ast.stmt]) -> bool:
    stack = list(body)
    while stack:
        node = stack.pop()
        if isinstance(node, ast.Continue):
            return True
        if isinstance(node, (ast.For, ast.AsyncFor, ast.While, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef, ast.Lambda)):
            if isinstance(node, (ast.For, ast.AsyncFor, ast.While)):
                stack.extend(node.orelse)       # continue in else belongs to the outer loop
            continue
        stack.extend(ast.iter_child_nodes(node))
    return False


def _stores_of(nodes, name: str) -> bool:
    for stmt in nodes:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, (ast.Store, ast.Del)):
                return True
            if isinstance(node, (ast.Global, ast.Nonlocal)) and name in node.names:
                return True
    return False


def _name_is_stable(name: str, body: list[ast.stmt]) -> bool:
    """`name` is neither rebound, mutated through a method/subscript, nor passed to a call in body."""
    if _stores_of(body, name):
        return False
    for stmt in body:
        for node in ast.walk(stmt):
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == name:
                return False
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id == name \
                    and isinstance(node.ctx, (ast.Store, ast.Del)):
                return False
            if isinstance(node, ast.Call):
                for arg in list(node.args) + [k.value for k in node.keywords]:
                    if isinstance(arg, ast.Name) and arg.id == name:
                        return False
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                return False
    return True


def _expr_is_stable(expr: ast.expr, body: list[ast.stmt]) -> bool:
    if isinstance(expr, ast.Constant):
        return True
    if isinstance(expr, ast.Name):
        return not _stores_of(body, expr.id)
    if isinstance(expr, ast.BinOp):
        return _expr_is_stable(expr.left, body) and _expr_is_stable(expr.right, body)
    if isinstance(expr, ast.UnaryOp):
        return _expr_is_stable(expr.operand, body)
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and expr.func.id == "len" \
            and len(expr.args) == 1 and not expr.keywords and isinstance(expr.args[0], ast.Name):
        return _name_is_stable(expr.args[0].id, body)
    return False


def _const_int(expr: ast.expr):
    if isinstance(expr, ast.Constant) and isinstance(expr.value, int) and not isinstance(expr.value, bool):
        return expr.value
    if isinstance(expr, ast.UnaryOp) and isinstance(expr.op, ast.USub):
        inner = _const_int(expr.operand)
        return -inner if inner is not None else None
    return None


def _py_loop_swap(text: str, rng: random.Random):
    tree = ast.parse(text)
    taken = _py_all_identifiers(tree) | _PY_BUILTINS | set(keyword.kwlist)
    scopes = [tree] + [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    eligible: dict[int, ast.For] = {}
    for scope in scopes:
        nodes = list(_py_scope_nodes(scope))
        loops = [n for n in nodes if isinstance(n, ast.For)]
        for loop in loops:
            if not (isinstance(loop.target, ast.Name) and isinstance(loop.iter, ast.Call)
                    and isinstance(loop.iter.func, ast.Name) and loop.iter.func.id == "range"
                    and 1 <= len(loop.iter.args) <= 3 and not loop.iter.keywords and not loop.orelse):
                continue
            if "range" in taken - _PY_BUILTINS and any(
                    isinstance(n, ast.Name) and n.id == "range" and isinstance(n.ctx, ast.Store)
                    for n in ast.walk(tree)):
                continue
            name = loop.target.id
            if _contains_continue(loop.body) or _stores_of(loop.body, name):
                continue
            if len(loop.iter.args) == 3:
                step = _const_int(loop.iter.args[2])
                if not step:
                    continue
            # Every other use of the loop variable in this scope must sit inside a for loop that
            # binds it itself; otherwise the value after the loop (stop vs. stop - 1) could leak.
            inside_binding_loops: set[int] = set()
            for other in loops:
                if isinstance(other.target, ast.Name) and other.target.id == name:
                    for stmt in other.body:
                        for sub in ast.walk(stmt):
                            inside_binding_loops.add(id(sub))
            safe = True
            for node in nodes:
                if isinstance(node, ast.Name) and node.id == name and isinstance(node.ctx, ast.Load) \
                        and id(node) not in inside_binding_loops:
                    safe = False
                    break
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)) and node is not scope:
                    if any(isinstance(s, ast.Name) and s.id == name for s in ast.walk(node)):
                        safe = False
                        break
            if safe:
                eligible[id(loop)] = loop
    if not eligible:
        return text, 0, []

    used_temp: set[str] = set()
    details: list[str] = []

    def temp_name() -> str:
        for candidate in ["limit", "upper", "stop_at", "end_index", "bound", "last_index", "n_steps"]:
            if candidate not in taken and candidate not in used_temp:
                used_temp.add(candidate)
                return candidate
        counter = 1
        while f"limit_{counter}" in taken or f"limit_{counter}" in used_temp:
            counter += 1
        used_temp.add(f"limit_{counter}")
        return f"limit_{counter}"

    class Swapper(ast.NodeTransformer):
        def visit_For(self, node):
            self.generic_visit(node)
            if id(node) not in eligible:
                return node
            name = node.target.id
            args = node.iter.args
            if len(args) == 1:
                start, stop, step = ast.Constant(0), args[0], 1
            else:
                start, stop = args[0], args[1]
                step = _const_int(args[2]) if len(args) == 3 else 1
            prefix: list[ast.stmt] = []
            if not _expr_is_stable(stop, node.body):
                tmp = temp_name()
                prefix.append(ast.Assign(targets=[ast.Name(tmp, ast.Store())], value=stop))
                stop = ast.Name(tmp, ast.Load())
            init = ast.Assign(targets=[ast.Name(name, ast.Store())], value=start)
            op = ast.Lt() if step > 0 else ast.Gt()
            test = ast.Compare(left=ast.Name(name, ast.Load()), ops=[op], comparators=[stop])
            increment = ast.AugAssign(target=ast.Name(name, ast.Store()),
                                      op=ast.Add() if step > 0 else ast.Sub(),
                                      value=ast.Constant(abs(step)))
            loop = ast.While(test=test, body=list(node.body) + [increment], orelse=[])
            details.append(f"line {node.lineno}: for {name} in range(...) -> while loop")
            return prefix + [init, loop]

    tree = Swapper().visit(tree)
    ast.fix_missing_locations(tree)
    new = ast.unparse(tree) + "\n"
    return new, len(details), details


# ---- dead_code -----------------------------------------------------------------------------------

_PY_DEAD_STATEMENTS = [
    ("debug_mode", "False"), ("retry_limit", "3"), ("scale_factor", "1.0"), ("log_prefix", "'[info]'"),
    ("temp_buffer", "[]"), ("unused_total", "0"), ("checkpoint", "None"), ("max_attempts", "5"),
    ("cache_hits", "0"), ("status_flag", "True"), ("trace_level", "2"), ("spare_items", "[]"),
]

_PY_HELPERS = [
    '''def {name}(values):
    if not values:
        return []
    top = max(values)
    scaled = []
    for value in values:
        scaled.append(value / top if top else 0)
    return scaled
''',
    '''def {name}(items, width):
    chunks = []
    current = []
    for item in items:
        current.append(item)
        if len(current) == width:
            chunks.append(current)
            current = []
    if current:
        chunks.append(current)
    return chunks
''',
    '''def {name}(value, low, high):
    if value < low:
        return low
    if value > high:
        return high
    return value
''',
]
_PY_HELPER_NAMES = ["normalise_values", "split_into_chunks", "clamp_value"]   # one per template


def _py_dead_code(text: str, rng: random.Random):
    tree = ast.parse(text)
    taken = _py_all_identifiers(tree) | _PY_BUILTINS | set(keyword.kwlist)
    functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    if not functions:
        raise ValueError("dead_code: no function to put dead code into")
    count = rng.randint(3, 6)
    pool = [item for item in _PY_DEAD_STATEMENTS if item[0] not in taken]
    rng.shuffle(pool)
    details: list[str] = []
    for name, value in pool[:count]:
        fn = rng.choice(functions)
        start = _py_body_start(fn.body)
        last = max(start, len(fn.body) - 1)
        pos = rng.randint(start, last)
        stmt = ast.parse(f"{name} = {value}").body[0]
        fn.body.insert(pos, stmt)
        details.append(f"unused variable {name} in {fn.name}()")
        taken.add(name)
    template_index = rng.randrange(len(_PY_HELPERS))
    helper_name = _PY_HELPER_NAMES[template_index]
    while helper_name in taken:
        helper_name += "_2"
    helper = ast.parse(_PY_HELPERS[template_index].format(name=helper_name)).body[0]
    slots = [i for i, s in enumerate(tree.body) if isinstance(s, (ast.FunctionDef, ast.AsyncFunctionDef))]
    position = rng.choice(slots) if slots else len(tree.body)
    tree.body.insert(position, helper)
    details.append(f"never-called helper {helper_name}()")
    ast.fix_missing_locations(tree)
    new = ast.unparse(tree) + "\n"
    return new, len(details), details


_PY_TRANSFORMS = {
    "rename": _py_rename,
    "comments_format": _py_comments_format,
    "reorder": _py_reorder,
    "loop_swap": _py_loop_swap,
    "dead_code": _py_dead_code,
}


# =============================================================================================
# C transforms (tree-sitter locates nodes; edits are applied to the text)
# =============================================================================================

_C_KEYWORDS = set("""auto break case char const continue default do double else enum extern float for goto
if inline int long register restrict return short signed sizeof static struct switch typedef union
unsigned void volatile while _Bool _Complex _Imaginary bool true false NULL""".split())

_C_LIBRARY = set("""printf scanf sprintf snprintf fprintf puts putchar getchar gets fgets fputs malloc calloc
realloc free exit abs labs fabs sqrt pow floor ceil round fmod exp log log10 sin cos tan atan atan2 strlen
strcpy strncpy strcat strncat strcmp strncmp strchr strrchr strstr strtok memset memcpy memmove memcmp
atoi atof atol strtol strtod qsort bsearch rand srand time isalpha isdigit isalnum isspace isupper
islower toupper tolower ispunct isxdigit stdout stderr stdin size_t FILE EOF main index""".split())


def _node_text(src: bytes, node) -> str:
    return src[node.start_byte:node.end_byte].decode("utf-8")


def _walk(node):
    stack = [node]
    while stack:
        cur = stack.pop()
        yield cur
        stack.extend(reversed(cur.children))


def _apply_edits(src: bytes, edits: list[tuple[int, int, str]]) -> bytes:
    edits = sorted(edits, key=lambda e: (e[0], e[1]))
    for (s1, e1, _), (s2, e2, _) in zip(edits, edits[1:]):
        if s2 < e1:
            raise ValueError("internal error: overlapping text edits")
    out = src
    for start, end, replacement in reversed(edits):
        out = out[:start] + replacement.encode("utf-8") + out[end:]
    return out


def _line_indent(src: bytes, pos: int) -> str:
    line_start = src.rfind(b"\n", 0, pos) + 1
    i = line_start
    while i < len(src) and src[i:i + 1] in (b" ", b"\t"):
        i += 1
    return src[line_start:i].decode("utf-8")


def _declarator_identifier(node):
    """The identifier inside a (possibly pointer / array / init) declarator, or None."""
    while node is not None:
        if node.type == "identifier":
            return node
        if node.type in ("init_declarator", "pointer_declarator", "array_declarator",
                         "parenthesized_declarator", "attributed_declarator"):
            inner = node.child_by_field_name("declarator")
            if inner is None:
                inner = next((c for c in node.named_children if c.type != "comment"), None)
            node = inner
            continue
        if node.type == "function_declarator":
            node = node.child_by_field_name("declarator")
            continue
        return None
    return None


def _c_function_name(fn) -> str | None:
    declarator = fn.child_by_field_name("declarator")
    while declarator is not None and declarator.type != "function_declarator":
        declarator = declarator.child_by_field_name("declarator")
    if declarator is None:
        return None
    ident = declarator.child_by_field_name("declarator")
    return ident.text.decode("utf-8") if ident is not None and ident.type == "identifier" else None


def _c_taken_names(src: bytes, root) -> set[str]:
    taken = set(_C_KEYWORDS) | set(_C_LIBRARY)
    for node in _walk(root):
        if node.type in ("identifier", "field_identifier", "type_identifier", "statement_identifier"):
            taken.add(_node_text(src, node))
        elif node.type.startswith("preproc") or node.type == "preproc_arg":
            taken.update(re.findall(r"[A-Za-z_]\w*", _node_text(src, node)))
    return taken


# ---- rename ----------------------------------------------------------------------------------

def _c_rename(text: str, rng: random.Random):
    src = text.encode("utf-8")
    root = _c_parse(src).root_node
    defined_functions = {name for fn in _walk(root) if fn.type == "function_definition"
                         for name in [_c_function_name(fn)] if name}
    macro_words: set[str] = set()
    for node in _walk(root):
        if node.type.startswith("preproc"):
            for child in node.children:
                if child.type in ("preproc_arg", "preproc_params"):
                    macro_words.update(re.findall(r"[A-Za-z_]\w*", _node_text(src, child)))
    candidates: list[str] = []

    def want(ident) -> None:
        if ident is None:
            return
        name = _node_text(src, ident)
        if name in ("main",) or name in _C_LIBRARY or name in _C_KEYWORDS or name in macro_words:
            return
        if name.startswith("__"):
            return
        if name not in candidates:
            candidates.append(name)

    for node in _walk(root):
        if node.type == "function_definition":
            name = _c_function_name(node)
            if name and name != "main":
                declarator = node.child_by_field_name("declarator")
                want(_declarator_identifier(declarator))
        elif node.type == "parameter_declaration":
            want(_declarator_identifier(node.child_by_field_name("declarator")))
        elif node.type == "declaration":
            for declarator in node.children_by_field_name("declarator"):
                ident = _declarator_identifier(declarator)
                if ident is None:
                    continue
                inner = declarator
                while inner is not None and inner.type in ("init_declarator", "pointer_declarator"):
                    inner = inner.child_by_field_name("declarator")
                if inner is not None and inner.type == "function_declarator":
                    # a prototype: rename only functions defined in this file
                    if _node_text(src, ident) not in defined_functions:
                        continue
                want(ident)
    if not candidates:
        return text, 0, []
    mapping = _build_mapping(candidates, _c_taken_names(src, root), rng)
    edits = []
    for node in _walk(root):
        if node.type == "identifier":
            name = _node_text(src, node)
            if name in mapping:
                edits.append((node.start_byte, node.end_byte, mapping[name]))
    new = _apply_edits(src, edits).decode("utf-8")
    return new, len(mapping), [f"{a} -> {b}" for a, b in mapping.items()]


# ---- comments_format ---------------------------------------------------------------------------

def _c_remove_comments(src: bytes) -> tuple[bytes, int]:
    root = _c_parse(src).root_node
    edits = []
    count = 0
    for node in _walk(root):
        if node.type != "comment":
            continue
        count += 1
        start, end = node.start_byte, node.end_byte
        line_start = src.rfind(b"\n", 0, start) + 1
        line_end = src.find(b"\n", end)
        if line_end == -1:
            line_end = len(src)
        before = src[line_start:start]
        after = src[end:line_end]
        if not before.strip() and not after.strip():
            # the comment owns its line(s): remove them including the newline
            edits.append((line_start, min(line_end + 1, len(src)), ""))
        elif not after.strip():
            # trailing comment: remove it and the spaces before it
            ws_start = start
            while ws_start > line_start and src[ws_start - 1:ws_start] in (b" ", b"\t"):
                ws_start -= 1
            edits.append((ws_start, end, ""))
        else:
            edits.append((start, end, " "))
    # remove duplicate whole-line edits (several comments on one line)
    unique = []
    seen = set()
    for edit in sorted(edits):
        if unique and edit[0] < unique[-1][1]:
            # overlapping: merge by extending the previous edit
            prev = unique[-1]
            unique[-1] = (prev[0], max(prev[1], edit[1]), prev[2] if prev[1] >= edit[1] else edit[2])
            continue
        if edit not in seen:
            unique.append(edit)
            seen.add(edit)
    return _apply_edits(src, unique), count


_BRACE_PARENTS = {"function_definition", "if_statement", "else_clause", "for_statement", "while_statement",
                  "do_statement", "switch_statement"}


def _c_brace_style(src: bytes, root) -> str:
    same_line = next_line = 0
    for node in _walk(root):
        if node.type == "function_definition":
            body = node.child_by_field_name("body")
            if body is None:
                continue
            between = src[node.start_byte:body.start_byte]
            if b"\n" in between.split(b")")[-1]:
                next_line += 1
            else:
                same_line += 1
    return "allman" if next_line > same_line else "knr"


def _c_switch_braces(src: bytes) -> tuple[bytes, str, int]:
    root = _c_parse(src).root_node
    style = _c_brace_style(src, root)
    edits = []
    for node in _walk(root):
        brace = None
        if node.type == "compound_statement" and node.parent is not None and node.parent.type in _BRACE_PARENTS:
            brace = node
        elif node.type in ("field_declaration_list", "enumerator_list"):
            brace = node
        if brace is not None:
            pos = brace.start_byte
            ws_start = pos
            while ws_start > 0 and src[ws_start - 1:ws_start] in (b" ", b"\t", b"\n", b"\r"):
                ws_start -= 1
            gap = src[ws_start:pos]
            if ws_start == 0:
                continue
            if style == "knr" and b"\n" not in gap:
                edits.append((ws_start, pos, "\n" + _line_indent(src, pos)))
            elif style == "allman" and b"\n" in gap:
                prev_line_start = src.rfind(b"\n", 0, ws_start) + 1
                prev_line = src[prev_line_start:ws_start]
                if prev_line.lstrip().startswith(b"#") or b"//" in prev_line or prev_line.rstrip().endswith(b"\\"):
                    continue
                edits.append((ws_start, pos, " "))
        if node.type == "else_clause":
            else_tok = node.children[0]
            pos = else_tok.start_byte
            ws_start = pos
            while ws_start > 0 and src[ws_start - 1:ws_start] in (b" ", b"\t", b"\n", b"\r"):
                ws_start -= 1
            if src[ws_start - 1:ws_start] != b"}":
                continue
            gap = src[ws_start:pos]
            if style == "knr" and b"\n" not in gap:
                edits.append((ws_start, pos, "\n" + _line_indent(src, ws_start - 1)))
            elif style == "allman" and b"\n" in gap:
                edits.append((ws_start, pos, " "))
    new_style = "allman" if style == "knr" else "knr"
    return _apply_edits(src, edits), f"{style} -> {new_style}", len(edits)


def _c_comments_format(text: str, rng: random.Random):
    src = text.encode("utf-8")
    src, removed = _c_remove_comments(src)
    src, style_change, brace_edits = _c_switch_braces(src)
    root = _c_parse(src).root_node
    function_lines = {}
    first_code_line = None
    for child in root.children:
        if child.type == "function_definition":
            function_lines[child.start_point[0]] = _c_function_name(child) or "function"
        if first_code_line is None and not child.type.startswith("preproc") and child.type != "comment":
            first_code_line = child.start_point[0]
    lines = src.decode("utf-8").split("\n")
    out: list[str] = [f"/* {rng.choice(_HEADER_PHRASES)} */"]
    added = 1
    use_line_comments = rng.random() < 0.5
    for index, line in enumerate(lines):
        previous = lines[index - 1] if index > 0 else ""
        if not line.strip() and not previous.rstrip().endswith("\\"):
            continue                                     # drop the old blank-line layout
        if index in function_lines:
            phrase = rng.choice(_COMMENT_PHRASES)
            name = function_lines[index]
            comment = f"// {name}: {phrase}" if use_line_comments else f"/* {name}: {phrase} */"
            out.extend(["", comment])
            added += 1
        elif index == first_code_line:
            out.append("")
        elif line.strip().startswith("return") and out and not out[-1].rstrip().endswith("{"):
            out.append("")
        out.append(line)
    new = "\n".join(out).rstrip("\n") + "\n"
    details = [f"removed {removed} comment(s)", f"added {added} comment(s)", f"brace style {style_change}",
               "blank-line layout changed"]
    return new, removed + added + brace_edits, details


# ---- reorder -------------------------------------------------------------------------------------

def _c_reorder(text: str, rng: random.Random):
    src = text.encode("utf-8")
    root = _c_parse(src).root_node
    children = [c for c in root.children]
    barrier = -1
    for i, child in enumerate(children):
        if child.type not in ("function_definition", "comment"):
            barrier = i
    region = [c for c in children[barrier + 1:] if c.type == "function_definition"]
    if len(region) < 2:
        raise ValueError("reorder: fewer than two movable function definitions")
    region_start = children[barrier].end_byte if barrier >= 0 else 0
    chunks = []
    previous_end = region_start
    for fn in region:
        chunks.append(src[previous_end:fn.end_byte].decode("utf-8").strip("\n"))
        previous_end = fn.end_byte
    tail = src[previous_end:].decode("utf-8")
    names = [_c_function_name(fn) or "?" for fn in region]
    order = list(range(len(chunks)))
    for _ in range(100):
        rng.shuffle(order)
        if order != sorted(order):
            break
    if order == sorted(order):
        order = order[1:] + order[:1]
    prototypes = []
    for fn in (c for c in _walk(root) if c.type == "function_definition"):
        name = _c_function_name(fn)
        if not name or name == "main":
            continue
        body = fn.child_by_field_name("body")
        header = src[fn.start_byte:body.start_byte].decode("utf-8").strip()
        header = re.sub(r"\s*\n\s*", " ", header)
        prototypes.append(header + ";")
    head = src[:region_start].decode("utf-8").rstrip("\n")
    pieces = [head, "", "\n".join(prototypes), ""]
    for i in order:
        pieces.append(chunks[i].strip("\n"))
        pieces.append("")
    new = "\n".join(pieces).rstrip("\n") + "\n" + tail.strip("\n") + ("\n" if tail.strip() else "")
    new = re.sub(r"\n{3,}", "\n\n", new)
    new_names = [names[i] for i in order]
    return new, len(prototypes) + 1, [f"inserted {len(prototypes)} prototype(s)",
                                      f"function order: {', '.join(new_names)}"]


# ---- loop_swap -----------------------------------------------------------------------------------

def _c_has_continue(body) -> bool:
    stack = [body]
    while stack:
        node = stack.pop()
        if node.type == "continue_statement":
            return True
        if node.type in ("goto_statement", "labeled_statement"):
            return True
        if node is not body and node.type in ("for_statement", "while_statement", "do_statement"):
            continue
        stack.extend(node.children)
    return False


def _c_declared_names(src: bytes, decl) -> list[str]:
    names = []
    for declarator in decl.children_by_field_name("declarator"):
        ident = _declarator_identifier(declarator)
        if ident is not None:
            names.append(_node_text(src, ident))
    return names


def _c_simple_init_assignments(src: bytes, decl) -> str | None:
    """`int i = 0, j = 5;` -> `i = 0, j = 5` (None if a declarator is not a plain initialised name)."""
    parts = []
    for declarator in decl.children_by_field_name("declarator"):
        if declarator.type != "init_declarator":
            return None
        inner = declarator.child_by_field_name("declarator")
        value = declarator.child_by_field_name("value")
        if inner is None or inner.type != "identifier" or value is None:
            return None
        parts.append(f"{_node_text(src, inner)} = {_node_text(src, value)}")
    return ", ".join(parts) if parts else None


def _c_eligible_for(src: bytes, node) -> bool:
    init = node.child_by_field_name("initializer")
    cond = node.child_by_field_name("condition")
    update = node.child_by_field_name("update")
    body = node.child_by_field_name("body")
    if init is None or cond is None or update is None or body is None:
        return False
    if _c_has_continue(body):
        return False
    if init.type == "declaration":
        names = _c_declared_names(src, init)
        if not names:
            return False
        # a declaration of the same name directly inside the body would capture the update
        if body.type == "compound_statement":
            for child in body.named_children:
                if child.type == "declaration" and set(_c_declared_names(src, child)) & set(names):
                    return False
    return True


def _c_convert_one_pass(src: bytes) -> tuple[bytes, list[str]]:
    root = _c_parse(src).root_node
    loops = [n for n in _walk(root) if n.type == "for_statement" and _c_eligible_for(src, n)]
    outer = []
    for loop in loops:
        p = loop.parent
        contained = False
        while p is not None:
            if p.type == "for_statement" and any(p.id == l.id for l in loops):
                contained = True
                break
            p = p.parent
        if not contained:
            outer.append(loop)
    if not outer:
        return src, []
    edits = []
    details = []
    introduced: dict[tuple[int, str], str] = {}     # (compound start, name) -> declaration type text
    for loop in outer:
        init = loop.child_by_field_name("initializer")
        cond = loop.child_by_field_name("condition")
        update = loop.child_by_field_name("update")
        body = loop.child_by_field_name("body")
        parent = loop.parent
        indent = _line_indent(src, loop.start_byte)
        cond_text = _node_text(src, cond)
        update_text = _node_text(src, update)
        close_paren = update.end_byte
        while src[close_paren:close_paren + 1] != b")":
            close_paren += 1
        gap_before_body = src[close_paren + 1:body.start_byte].decode("utf-8")

        wrap = parent is None or parent.type != "compound_statement"
        init_stmt = None
        if init.type == "declaration":
            names = _c_declared_names(src, init)
            type_text = _node_text(src, init.child_by_field_name("type"))
            if not wrap:
                compound_key = parent.start_byte
                conflict = False
                reuse = True
                for name in names:
                    key = (compound_key, name)
                    if key in introduced:
                        if introduced[key] != type_text:
                            conflict = True
                        continue
                    reuse = False
                    # existing declaration of the same name in this block (or the function's params)
                    for child in parent.named_children:
                        if child.type == "declaration" and name in _c_declared_names(src, child):
                            conflict = True
                    if parent.parent is not None and parent.parent.type == "function_definition":
                        for param in _walk(parent.parent.child_by_field_name("declarator")):
                            if param.type == "parameter_declaration":
                                ident = _declarator_identifier(param.child_by_field_name("declarator"))
                                if ident is not None and _node_text(src, ident) == name:
                                    conflict = True
                    # later uses of the name in this block (outside for loops that redeclare it)
                    for sibling in parent.named_children:
                        if sibling.start_byte < loop.end_byte:
                            continue
                        if sibling.type == "for_statement":
                            s_init = sibling.child_by_field_name("initializer")
                            if s_init is not None and s_init.type == "declaration" \
                                    and name in _c_declared_names(src, s_init):
                                continue
                        if any(n.type == "identifier" and _node_text(src, n) == name for n in _walk(sibling)):
                            conflict = True
                if conflict:
                    wrap = True
                elif reuse:
                    assignments = _c_simple_init_assignments(src, init)
                    if assignments is None:
                        wrap = True
                    else:
                        init_stmt = assignments + ";"
                if not wrap and init_stmt is None:
                    init_stmt = _node_text(src, init).rstrip()
                    if not init_stmt.endswith(";"):
                        init_stmt += ";"
                    for name in names:
                        introduced[(compound_key, name)] = type_text
            if wrap:
                init_stmt = _node_text(src, init).rstrip()
                if not init_stmt.endswith(";"):
                    init_stmt += ";"
        else:
            init_stmt = _node_text(src, init) + ";"

        # new body: original body plus the update as its last statement
        if body.type == "compound_statement":
            inner_children = [c for c in body.children if c.type not in ("{", "}")]
            if inner_children:
                last = inner_children[-1]
                inner_indent = _line_indent(src, last.start_byte)
                if not inner_indent or _line_indent(src, last.start_byte) == indent and \
                        src.rfind(b"\n", body.start_byte, last.start_byte) == -1:
                    inner_indent = indent + "    "
                insert_at = last.end_byte
            else:
                inner_indent = indent + "    "
                insert_at = body.start_byte + 1
            body_text = (src[body.start_byte:insert_at].decode("utf-8") + "\n" + inner_indent + update_text +
                         ";" + src[insert_at:body.end_byte].decode("utf-8"))
            if src.rfind(b"\n", insert_at, body.end_byte) == -1:
                # closing brace was on the same line as the last statement
                pass
        else:
            inner_indent = indent + "    "
            body_text = ("{\n" + inner_indent + _node_text(src, body) + "\n" + inner_indent + update_text +
                         ";\n" + indent + "}")
            gap_before_body = " "
        while_text = f"while ({cond_text}){gap_before_body}{body_text}"
        if wrap:
            replacement = "{\n" + indent + "    " + init_stmt + "\n" + indent + "    " + \
                while_text.replace("\n", "\n    ") + "\n" + indent + "}"
        else:
            replacement = init_stmt + "\n" + indent + while_text
        edits.append((loop.start_byte, loop.end_byte, replacement))
        details.append(f"line {loop.start_point[0] + 1}: for -> while" + (" (braced block)" if wrap else ""))
    return _apply_edits(src, edits), details


def _c_loop_swap(text: str, rng: random.Random):
    src = text.encode("utf-8")
    details: list[str] = []
    for _ in range(50):
        new_src, step_details = _c_convert_one_pass(src)
        if not step_details:
            break
        if c_tree_has_errors(_c_parse(new_src)):
            raise ValueError("loop_swap: conversion produced invalid C")
        src = new_src
        details.extend(step_details)
    return src.decode("utf-8"), len(details), details


# ---- dead_code -----------------------------------------------------------------------------------

_C_DEAD_DECLS = [
    ("int", "unused_counter", "0"), ("double", "scale_factor", "1.0"), ("int", "debug_level", "0"),
    ("char", "status_flag", "'y'"), ("long", "checksum", "0L"), ("int", "retry_limit", "3"),
    ("double", "epsilon", "1e-9"), ("unsigned int", "spare_bits", "0u"), ("int", "trace_on", "0"),
    ("float", "ratio_hint", "0.5f"),
]

_C_HELPERS = [
    """int {name}(int value, int low, int high)
{{
    if (value < low) {{
        return low;
    }}
    if (value > high) {{
        return high;
    }}
    return value;
}}""",
    """int {name}(const int values[], int count)
{{
    int best = 0;
    int pos;
    for (pos = 1; pos < count; pos++) {{
        if (values[pos] > values[best]) {{
            best = pos;
        }}
    }}
    return best;
}}""",
    """double {name}(double total, int parts)
{{
    if (parts <= 0) {{
        return 0.0;
    }}
    return total / parts;
}}""",
]
_C_HELPER_NAMES = ["clamp_value", "index_of_largest", "safe_average"]   # one per template


def _c_dead_code(text: str, rng: random.Random):
    src = text.encode("utf-8")
    root = _c_parse(src).root_node
    taken = _c_taken_names(src, root)
    functions = [n for n in _walk(root) if n.type == "function_definition"]
    if not functions:
        raise ValueError("dead_code: no function to put dead code into")
    count = rng.randint(3, 6)
    pool = [d for d in _C_DEAD_DECLS if d[1] not in taken]
    rng.shuffle(pool)
    per_function: dict[int, list[str]] = {}
    details = []
    for type_text, name, value in pool[:count]:
        fn = rng.choice(functions)
        per_function.setdefault(fn.start_byte, []).append(f"{type_text} {name} = {value};")
        details.append(f"unused variable {name} in {_c_function_name(fn)}()")
    edits = []
    for fn in functions:
        decls = per_function.get(fn.start_byte)
        if not decls:
            continue
        body = fn.child_by_field_name("body")
        inner = [c for c in body.children if c.type not in ("{", "}")]
        indent = _line_indent(src, inner[0].start_byte) if inner else "    "
        if not indent:
            indent = "    "
        text_insert = "".join("\n" + indent + d for d in decls)
        edits.append((body.start_byte + 1, body.start_byte + 1, text_insert))
    template_index = rng.randrange(len(_C_HELPERS))
    helper_name = _C_HELPER_NAMES[template_index]
    while helper_name in taken:
        helper_name += "_2"
    helper = _C_HELPERS[template_index].format(name=helper_name)
    main_fn = next((f for f in root.children if f.type == "function_definition" and _c_function_name(f) == "main"),
                   None)
    if main_fn is not None:
        edits.append((main_fn.start_byte, main_fn.start_byte, helper + "\n\n"))
    else:
        edits.append((len(src), len(src), "\n" + helper + "\n"))
    details.append(f"never-called helper {helper_name}()")
    new = _apply_edits(src, edits).decode("utf-8")
    return new, len(details), details


_C_TRANSFORMS = {
    "rename": _c_rename,
    "comments_format": _c_comments_format,
    "reorder": _c_reorder,
    "loop_swap": _c_loop_swap,
    "dead_code": _c_dead_code,
}
