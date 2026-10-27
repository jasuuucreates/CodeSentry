"""Normalization: turn raw tokens into the canonical symbol stream used for fingerprinting.

Each token is replaced by a symbol that keeps the *shape* of the code and forgets the details
a plagiarist can change for free:

* every identifier becomes ``ID``, so renaming variables or functions cannot change the stream;
* every number / string / character literal becomes ``NUM`` / ``STR`` / ``CHR``;
* keywords and operators stay as their own text (``for``, ``+=``), because they ARE the shape;
* ``INDENT`` / ``DEDENT`` stay, because in Python indentation is block structure;
* comments and preprocessor lines are removed, and line breaks and spaces were never tokens,
  so comments and formatting never reach the stream.

Each normalized token still carries the original text and source position, so a matching
region found later can be mapped back to real lines of the submission.
"""
from __future__ import annotations

from .lang import SUPPORTED_EXTENSIONS
from .models import EngineError, Token

# Token kinds whose symbol is a fixed placeholder, independent of the token's text.
_PLACEHOLDER_SYMBOLS: dict[str, str] = {
    "IDENT": "ID",
    "NUMBER": "NUM",
    "STRING": "STR",
    "CHAR": "CHR",
    "INDENT": "INDENT",
    "DEDENT": "DEDENT",
}
# Token kinds whose symbol is the token's own text.
_SPELLED_KINDS = frozenset({"KEYWORD", "OP"})
# Token kinds that never reach the symbol stream.
_REMOVED_KINDS = frozenset({"COMMENT", "PREPROC"})

_LANGUAGES = frozenset(SUPPORTED_EXTENSIONS.values())


def normalize(tokens: list[Token], language: str) -> list[Token]:
    """Return a NEW list of tokens whose `kind` is the canonical symbol.

    `value`, `line`, `col`, `end_line` and `end_col` are copied unchanged. Both tokenizers emit
    the same token kinds, so the mapping is identical for Python and C; `language` is checked
    so that a caller passing an unsupported language fails loudly instead of silently.
    Raises :class:`EngineError` for an unsupported language or an unknown token kind.
    """
    if language not in _LANGUAGES:
        raise EngineError(f"unsupported language {language!r}")

    normalized: list[Token] = []
    for tok in tokens:
        kind = tok.kind
        if kind in _REMOVED_KINDS:
            continue
        symbol = tok.value if kind in _SPELLED_KINDS else _PLACEHOLDER_SYMBOLS.get(kind)
        if symbol is None:
            raise EngineError(f"unknown token kind {kind!r} at line {tok.line}")
        normalized.append(Token(symbol, tok.value, tok.line, tok.col, tok.end_line, tok.end_col))
    return normalized


def symbols(normalized: list[Token]) -> list[str]:
    """The symbol stream itself, e.g. ``['ID', '=', 'NUM']``: what winnowing hashes."""
    return [tok.kind for tok in normalized]
