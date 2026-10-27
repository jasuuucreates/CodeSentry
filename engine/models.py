"""Core data model shared by every engine module.

Everything the detection engine passes between its stages is defined here, so that the
tokenizers, the winnowing stage, the structural stage and the pipeline all speak the same
language. See docs/ARCHITECTURE_CONTRACT.md, section 2.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields


class EngineError(ValueError):
    """Base class for every error the detection engine raises deliberately."""


class TokenizeError(EngineError):
    """The source text could not be split into tokens."""


class StructureError(EngineError):
    """The source text could not be parsed into a syntax tree."""


@dataclass(frozen=True)
class Token:
    """One lexical token.

    `line` and `end_line` are 1-based; `col` and `end_col` are 0-based, `end_col` exclusive.
    After normalization `kind` holds the canonical symbol (for example ``'ID'`` or ``'+='``)
    while `value` still holds the original source text.
    """

    kind: str
    value: str
    line: int
    col: int
    end_line: int
    end_col: int


@dataclass
class SourceFile:
    """A submission as the engine sees it."""

    id: int
    name: str
    language: str
    text: str


@dataclass(frozen=True)
class Fingerprint:
    """A k-gram hash selected by winnowing, with the source position it came from."""

    hash: int
    start: int
    end: int
    line_start: int
    line_end: int


@dataclass
class Node:
    """A node of a canonical syntax skeleton: a label and ordered children.

    Identifier names and literal values never appear in a label, which is what makes the
    skeleton immune to renaming.
    """

    label: str
    children: list[Node] = field(default_factory=list)

    def size(self) -> int:
        """Number of nodes in this subtree (iterative, so deep trees cannot overflow the stack)."""
        count = 0
        stack = [self]
        while stack:
            node = stack.pop()
            count += 1
            stack.extend(node.children)
        return count

    def to_dict(self, max_depth: int | None = None) -> dict:
        """Nested ``{"label", "children"}`` dictionaries, preserving child order.

        When `max_depth` cuts a subtree off, that node gets ``"truncated": True`` so a viewer can
        show that more structure exists below it.
        """
        root: dict = {"label": self.label, "children": []}
        stack: list[tuple[Node, dict, int]] = [(self, root, 0)]
        while stack:
            node, out, depth = stack.pop()
            if max_depth is not None and depth >= max_depth:
                if node.children:
                    out["truncated"] = True
                continue
            for child in node.children:
                child_out: dict = {"label": child.label, "children": []}
                out["children"].append(child_out)
                stack.append((child, child_out, depth + 1))
        return root


@dataclass
class MatchRegion:
    """A block of lines in file A that matches a block of lines in file B (1-based, inclusive)."""

    a_start: int
    a_end: int
    b_start: int
    b_end: int
    tokens: int

    def to_dict(self) -> dict:
        return asdict(self)


# Allowed range for every tunable setting: (minimum, maximum).
_RANGES: dict[str, tuple[float, float]] = {
    "k": (2, 50),
    "w": (1, 100),
    "w_token": (0.0, 1.0),
    "w_structure": (0.0, 1.0),
    "high_threshold": (0.0, 1.0),
    "moderate_threshold": (0.0, 1.0),
    "ted_node_cap": (10, 5000),
}


@dataclass
class EngineConfig:
    """Tunable settings of the detection engine."""

    k: int = 5                      # k-gram length, in normalized tokens
    w: int = 4                      # winnowing window size
    w_token: float = 0.5            # fusion weight of the token (winnowing) score
    w_structure: float = 0.5        # fusion weight of the structural (AST) score
    high_threshold: float = 0.75
    moderate_threshold: float = 0.50
    ted_node_cap: int = 200         # above this many nodes, tree edit distance is approximated

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict | None) -> EngineConfig:
        """Build a configuration from user input, e.g. HTML form fields that arrive as strings.

        Unknown keys and empty values are ignored; out-of-range or malformed values raise
        :class:`EngineError` with a message that can be shown to the user.
        """
        if d is None:
            return cls()
        if not isinstance(d, dict):
            raise EngineError("configuration must be a JSON object")

        values: dict = {}
        for f in fields(cls):
            if f.name not in d or d[f.name] is None or d[f.name] == "":
                continue
            raw = d[f.name]
            if isinstance(raw, bool):
                raise EngineError(f"{f.name} must be a number, not true/false")
            try:
                number = float(raw)
            except (TypeError, ValueError):
                raise EngineError(f"{f.name} must be a number (got {raw!r})") from None

            wants_int = isinstance(f.default, int)
            if wants_int:
                if not number.is_integer():
                    raise EngineError(f"{f.name} must be a whole number (got {raw!r})")
                value: float = int(number)
            else:
                value = number

            low, high = _RANGES[f.name]
            if not low <= value <= high:
                raise EngineError(f"{f.name} must be between {low:g} and {high:g} (got {raw!r})")
            values[f.name] = value

        config = cls(**values)
        if config.w_token + config.w_structure <= 0:
            raise EngineError("w_token and w_structure cannot both be 0")
        if config.moderate_threshold > config.high_threshold:
            raise EngineError("moderate_threshold cannot be greater than high_threshold")
        return config
