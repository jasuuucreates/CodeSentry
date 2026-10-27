"""Python tokenizer: splits Python source text into CodeSentry tokens.

Instead of writing our own Python lexer we reuse the standard library's `tokenize` module. It
is the reference tokenizer of the language, so it already knows every string prefix,
f-strings, numeric literal form and the indentation rules; our tokens are exactly Python's
tokens, only relabelled with the engine's token kinds (contract section 3).

The engine targets CPython 3.11, where `tokenize` returns an f-string as one STRING token.
"""
from __future__ import annotations

import io
import keyword
import tokenize

from .models import Token, TokenizeError

# Python token types we keep, and the engine kind each becomes. NAME is handled separately
# because it splits into KEYWORD and IDENT. Every other type is dropped on purpose: NEWLINE and
# NL only mark line ends (layout, which must not affect similarity) and ENDMARKER marks the end
# of the file. ERRORTOKEN is handled separately because it means the text is not valid Python.
_KIND_BY_TYPE: dict[int, str] = {
    tokenize.NUMBER: "NUMBER",
    tokenize.STRING: "STRING",
    tokenize.OP: "OP",
    tokenize.COMMENT: "COMMENT",
    tokenize.INDENT: "INDENT",
    tokenize.DEDENT: "DEDENT",
}

_OPENING_BRACKETS = frozenset("([{")
_CLOSING_BRACKETS = frozenset(")]}")


def tokenize_python(text: str) -> list[Token]:
    """Tokenize Python source code.

    Returns tokens with kinds KEYWORD, IDENT, NUMBER, STRING, OP, COMMENT, INDENT and DEDENT,
    each with its exact text and 1-based line / 0-based column start and end positions.
    Raises :class:`TokenizeError` with a ``"line N: ..."`` message when the text is not valid
    Python at the lexical level (unterminated string, unclosed bracket, bad indentation,
    a character that cannot start any token).
    """
    # Python itself reads source files with universal newlines ("\r\n" and a lone "\r" both
    # mean a line break). `tokenize` only understands "\n", so translate first; line numbers
    # then match what Python would report for the same file.
    source = text.replace("\r\n", "\n").replace("\r", "\n")
    # A UTF-8 byte-order mark saved by some Windows editors is not part of the program.
    if source.startswith("﻿"):
        source = source[1:]
    # Without a final newline `tokenize` has to guess where the last statement ends; giving it
    # the newline makes the last line behave exactly like every other line.
    if not source.endswith("\n"):
        source += "\n"

    last_line = source.count("\n")
    tokens: list[Token] = []
    # Brackets still open, as (bracket, line). Only used to say WHERE an unclosed bracket was
    # opened, because `tokenize` itself only notices the problem at the end of the file.
    open_brackets: list[tuple[str, int]] = []

    try:
        for tok in tokenize.generate_tokens(io.StringIO(source).readline):
            (line, col), (end_line, end_col) = tok.start, tok.end
            tok_type = tok.type

            if tok_type == tokenize.NAME:
                kind = "KEYWORD" if keyword.iskeyword(tok.string) else "IDENT"
            elif tok_type == tokenize.ERRORTOKEN:
                # `tokenize` reports the blanks in front of a bad character as separate error
                # tokens; skip those so the message names the character that is really wrong.
                if tok.string.isspace():
                    continue
                raise TokenizeError(_error_token_message(tok.string, line))
            else:
                kind = _KIND_BY_TYPE.get(tok_type)
                if kind is None:
                    continue
                if kind == "OP":
                    if tok.string in _OPENING_BRACKETS:
                        open_brackets.append((tok.string, line))
                    elif tok.string in _CLOSING_BRACKETS and open_brackets:
                        open_brackets.pop()
                elif kind == "DEDENT" and line > last_line:
                    # Blocks still open when the file ends are closed by DEDENTs that `tokenize`
                    # places on the line AFTER the last line, which does not exist. Attach them
                    # to the end of the last token instead, so every token lies inside the file
                    # and a matched region can never point past the final line. (A DEDENT always
                    # follows an INDENT, so `tokens` is not empty here.)
                    line = end_line = tokens[-1].end_line
                    col = end_col = tokens[-1].end_col

            tokens.append(Token(kind, tok.string, line, col, end_line, end_col))

    except tokenize.TokenError as exc:
        # Raised only at the end of the file: args are (message, (line, column)).
        message, (line, _col) = exc.args
        if "string" in message:
            detail = f"line {line}: unterminated triple-quoted string"
        elif open_brackets:
            bracket, bracket_line = open_brackets[-1]
            detail = f"line {bracket_line}: '{bracket}' was never closed"
        else:
            detail = f"line {line}: unexpected end of file ({message})"
        raise TokenizeError(detail) from None
    except SyntaxError as exc:
        # IndentationError is a subclass of SyntaxError, so this covers both.
        raise TokenizeError(f"line {exc.lineno}: {exc.msg}") from None

    return tokens


def _error_token_message(char: str, line: int) -> str:
    """Human-readable message for a character `tokenize` could not start a token with."""
    if char in ("'", '"'):
        return f"line {line}: unterminated string literal"
    return f"line {line}: unexpected character {char!r}"
