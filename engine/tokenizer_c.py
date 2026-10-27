"""C tokenizer: a hand-written, single-pass, longest-match lexer.

The whole idea in one sentence: stand at the current character, decide from that character
which kind of token can start here, consume the LONGEST valid token of that kind, record where
it started and where it ended, and continue right after it. Every character is looked at a
constant number of times, so the running time grows linearly with the file length (O(n)).

Small compiled regular expressions consume the *body* of a token once its kind is known (the
digits of a number, the inside of a string); the decisions are explicit Python code below.

tree-sitter is deliberately not used here: the token stage must work even on a file that does
not parse cleanly, and it must not depend on the structural stage.
"""
from __future__ import annotations

import re

from .models import Token, TokenizeError

C_KEYWORDS: frozenset[str] = frozenset(
    (
        "auto break case char const continue default do double else enum extern float for goto "
        "if inline int long register restrict return short signed sizeof static struct switch "
        "typedef union unsigned void volatile while _Bool _Complex _Imaginary"
    ).split()
)

# Every C operator and punctuator, LONGEST FIRST. Order matters: C's "maximal munch" rule says
# the lexer must always take the longest operator that fits, so trying longer spellings before
# shorter ones makes `a+++b` come out as `a ++ + b` and `x>>=1` as `x >>= 1`, exactly as a C
# compiler reads them.
C_OPERATORS: tuple[str, ...] = tuple(
    sorted(
        {
            ">>=", "<<=", "...",
            "->", "++", "--", "<<", ">>", "<=", ">=", "==", "!=", "&&", "||",
            "+=", "-=", "*=", "/=", "%=", "&=", "|=", "^=", "##",
            "+", "-", "*", "/", "%", "=", "<", ">", "!", "~", "&", "|", "^",
            "?", ":", ";", ",", ".", "(", ")", "[", "]", "{", "}", "#",
        },
        key=lambda op: (-len(op), op),
    )
)

# Encoding prefixes that turn the literal right after them into a wide/Unicode literal (L"x").
_LITERAL_PREFIXES = frozenset({"L", "u", "U", "u8"})
_DIGITS = frozenset("0123456789")
_BLANKS = frozenset(" \t\f\v")

_BLANKS_RE = re.compile(r"[ \t\f\v]+")
_IDENT_RE = re.compile(r"[^\W\d]\w*")  # a letter or underscore, then letters, digits, underscores
_NUMBER_RE = re.compile(
    r"""
    (?:
        0[xX](?:[0-9a-fA-F]+\.?[0-9a-fA-F]*|\.[0-9a-fA-F]+)(?:[pP][+-]?[0-9]+)?   # hexadecimal
      | 0[bB][01]+                                                             # binary
      | (?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?  # decimal, octal (0755), float, 1.5e-3
    )
    [uUlLfF]*                                             # suffixes: u l ul ull f, any case
    """,
    re.VERBOSE,
)
# A string literal: ordinary characters, or a backslash escaping the next character (which may
# be a line break: a backslash-continued string). The pattern is written "unrolled" (no nested
# alternatives that can match the same text), so a missing closing quote fails in linear time.
_STRING_RE = re.compile(r'"[^"\\\r\n]*(?:\\(?:\r\n|[\s\S])[^"\\\r\n]*)*"')
_CHAR_RE = re.compile(r"'[^'\\\r\n]*(?:\\(?:\r\n|[\s\S])[^'\\\r\n]*)*'")
# Inside a preprocessor line quotes only need to hide comment markers, and free text such as
# `#error don't do this` is legal, so there the closing quote is optional.
_DIRECTIVE_STRING_RE = re.compile(r'"[^"\\\r\n]*(?:\\(?:\r\n|[\s\S])[^"\\\r\n]*)*"?')
_DIRECTIVE_CHAR_RE = re.compile(r"'[^'\\\r\n]*(?:\\(?:\r\n|[\s\S])[^'\\\r\n]*)*'?")
_DIRECTIVE_TEXT_RE = re.compile(r"[^\r\n\\/\"']+")
# `//` runs to the end of the line, and C joins a line ending in a backslash with the next one
# (even inside a comment). In a comment a backslash escapes nothing else.
_LINE_COMMENT_RE = re.compile(r"//[^\r\n\\]*(?:\\(?:\r\n|[\r\n])?[^\r\n\\]*)*")
# A backslash, together with the line break right after it if there is one (a "line splice").
_SPLICE_RE = re.compile(r"\\(?:\r\n|[\r\n])?")


def _operators_by_first_char(operators: tuple[str, ...]) -> dict[str, tuple[str, ...]]:
    """Group the operator table by first character, keeping the longest-first order.

    The lexer then only tries the few operators that can start with the current character.
    """
    groups: dict[str, tuple[str, ...]] = {}
    for op in operators:
        groups[op[0]] = groups.get(op[0], ()) + (op,)
    return groups


_OPERATORS_BY_FIRST_CHAR = _operators_by_first_char(C_OPERATORS)


def tokenize_c(text: str) -> list[Token]:
    """Tokenize C source code.

    Returns tokens with kinds KEYWORD, IDENT, NUMBER, STRING, CHAR, OP, COMMENT and PREPROC,
    each with its exact source text and 1-based line / 0-based column start and end positions
    ("\\r\\n", "\\n" and a lone "\\r" each count as one line break). Raises
    :class:`TokenizeError` with a ``"line N: ..."`` message for an unterminated string,
    character constant or block comment, or a character that cannot start any C token.
    """
    tokens: list[Token] = []
    append = tokens.append
    n = len(text)
    # A UTF-8 byte-order mark saved by some Windows editors is not part of the program; starting
    # line 1 after it keeps the columns of line 1 equal to what an editor shows.
    i = line_start = 1 if text.startswith("\ufeff") else 0
    line = 1              # line number of position i
    # line_start is the index in `text` where the current line begins, so column = i - line_start.
    at_line_start = True  # only blanks or comments so far on this line: '#' starts a directive

    while i < n:
        ch = text[i]

        if ch in _BLANKS:
            i = _BLANKS_RE.match(text, i).end()
            continue
        if ch == "\n" or ch == "\r":
            i += 2 if text.startswith("\r\n", i) else 1
            line += 1
            line_start = i
            at_line_start = True
            continue

        col = i - line_start
        spans_lines = False  # only comments, directives and literals can contain a line break

        if ch == "_" or ch.isalpha():
            j = _IDENT_RE.match(text, i).end()
            word = text[i:j]
            if j < n and (text[j] == '"' or text[j] == "'") and word in _LITERAL_PREFIXES:
                kind, j = _scan_literal(text, j, line)
                spans_lines = True
            elif word in C_KEYWORDS:
                kind = "KEYWORD"
            else:
                kind = "IDENT"
        elif ch in _DIGITS or (ch == "." and i + 1 < n and text[i + 1] in _DIGITS):
            j = _NUMBER_RE.match(text, i).end()
            kind = "NUMBER"
        elif ch == '"' or ch == "'":
            kind, j = _scan_literal(text, i, line)
            spans_lines = True
        elif text.startswith("//", i):
            j = _LINE_COMMENT_RE.match(text, i).end()
            kind = "COMMENT"
            spans_lines = True
        elif text.startswith("/*", i):
            # Searching from i + 2 makes sure the '*' of the opening "/*" cannot also close it.
            close = text.find("*/", i + 2)
            if close < 0:
                raise TokenizeError(f"line {line}: unterminated block comment")
            j = close + 2
            kind = "COMMENT"
            spans_lines = True
        elif ch == "#" and at_line_start:
            j = _directive_end(text, i, line)
            kind = "PREPROC"
            spans_lines = True
        elif ch == "\\":
            # A backslash at the end of a line joins it with the next line; the joined halves
            # are one logical line, so `at_line_start` is left as it was.
            j = _SPLICE_RE.match(text, i).end()
            if j == i + 1:
                raise TokenizeError(f"line {line}: unexpected character '\\' (column {col + 1})")
            line += 1
            line_start = i = j
            continue
        else:
            op = _match_operator(text, i, ch)
            if op is None:
                raise TokenizeError(f"line {line}: unexpected character {ch!r} (column {col + 1})")
            j = i + len(op)
            kind = "OP"

        start_line = line
        if spans_lines:
            line, line_start = _advance_lines(text, i, j, line, line_start)
        append(Token(kind, text[i:j], start_line, col, line, j - line_start))
        # A comment is replaced by a space before C looks for directives, so `/* c */ #define`
        # is still a directive: comments do not end the "start of line" state.
        if kind != "COMMENT":
            at_line_start = False
        i = j

    return tokens


def _match_operator(text: str, i: int, ch: str) -> str | None:
    """The longest operator starting at `i` (`ch` is ``text[i]``), or None if there is none."""
    for op in _OPERATORS_BY_FIRST_CHAR.get(ch, ()):
        if text.startswith(op, i):
            return op
    return None


def _scan_literal(text: str, quote: int, line: int) -> tuple[str, int]:
    """Consume the string or character literal whose opening quote is at index `quote`.

    Returns ``(kind, end_index)``. Escapes such as ``\\"`` and ``'\\''`` are handled by the
    patterns: a backslash always takes the character after it, so it can never end the literal.
    """
    if text[quote] == '"':
        match = _STRING_RE.match(text, quote)
        if match is None:
            raise TokenizeError(f"line {line}: unterminated string literal")
        return "STRING", match.end()
    match = _CHAR_RE.match(text, quote)
    if match is None:
        raise TokenizeError(f"line {line}: unterminated character constant")
    if match.end() - quote == 2:
        raise TokenizeError(f"line {line}: empty character constant ''")
    return "CHAR", match.end()


def _directive_end(text: str, hash_index: int, line: int) -> int:
    """Index just past the preprocessor directive whose '#' is at `hash_index`.

    A directive runs to the end of its line. A backslash before the line break continues it on
    the next line, and a block comment that starts inside it and closes on a later line carries
    it along to that line. Quotes are honoured so that ``"/*"`` inside ``#define`` text is not
    taken for a comment.
    """
    n = len(text)
    j = hash_index + 1
    while j < n:
        ch = text[j]
        if ch == "\n" or ch == "\r":
            break
        if ch == "\\":
            j = _SPLICE_RE.match(text, j).end()
        elif ch == "/":
            if text.startswith("/*", j):
                close = text.find("*/", j + 2)
                if close < 0:
                    comment_line = line + _count_line_breaks(text, hash_index, j)
                    raise TokenizeError(f"line {comment_line}: unterminated block comment")
                j = close + 2
            elif text.startswith("//", j):
                j = _LINE_COMMENT_RE.match(text, j).end()
            else:
                j += 1
        elif ch == '"':
            j = _DIRECTIVE_STRING_RE.match(text, j).end()
        elif ch == "'":
            j = _DIRECTIVE_CHAR_RE.match(text, j).end()
        else:
            j = _DIRECTIVE_TEXT_RE.match(text, j).end()
    return j


def _count_line_breaks(text: str, start: int, end: int) -> int:
    """Line breaks in ``text[start:end]``, where "\\r\\n" is ONE break (not two)."""
    return text.count("\n", start, end) + text.count("\r", start, end) - text.count("\r\n", start, end)


def _advance_lines(text: str, start: int, end: int, line: int, line_start: int) -> tuple[int, int]:
    """New ``(line, line_start)`` after consuming ``text[start:end]``."""
    breaks = _count_line_breaks(text, start, end)
    if not breaks:
        return line, line_start
    last_break = max(text.rfind("\n", start, end), text.rfind("\r", start, end))
    return line + breaks, last_break + 1
