"""Raw tokenizers (contract section 3)."""
import pytest

from engine.models import TokenizeError
from engine.tokenizer_c import tokenize_c
from engine.tokenizer_python import tokenize_python


def kinds_values(tokens):
    return [(t.kind, t.value) for t in tokens]


# ---- Python ------------------------------------------------------------------------------------

def test_python_basic_kinds_and_comment():
    tokens = tokenize_python("x = 1  # note\n")
    assert kinds_values(tokens) == [("IDENT", "x"), ("OP", "="), ("NUMBER", "1"), ("COMMENT", "# note")]


def test_python_keywords_strings_and_positions():
    tokens = tokenize_python("for name in items:\n    print('hi', name)\n")
    assert tokens[0].kind == "KEYWORD" and tokens[0].value == "for"
    assert ("KEYWORD", "in") in kinds_values(tokens)
    assert ("IDENT", "print") in kinds_values(tokens)          # builtins are ordinary names
    assert ("STRING", "'hi'") in kinds_values(tokens)
    first = tokens[0]
    assert (first.line, first.col, first.end_line, first.end_col) == (1, 0, 1, 3)


def test_python_indent_dedent_kept_newlines_dropped():
    tokens = tokenize_python("if x:\n    y = 2\nz = 3\n")
    kinds = [t.kind for t in tokens]
    assert "INDENT" in kinds and "DEDENT" in kinds
    assert all(t.kind not in ("NEWLINE", "NL", "ENCODING", "ENDMARKER") for t in tokens)
    assert kinds.index("INDENT") < kinds.index("DEDENT")


def test_python_unclosed_bracket_raises_tokenize_error():
    with pytest.raises(TokenizeError):
        tokenize_python("values = (1,\n2,\n")


def test_python_bad_dedent_raises_tokenize_error():
    with pytest.raises(TokenizeError) as info:
        tokenize_python("if x:\n        a = 1\n    b = 2\n")
    assert "3" in str(info.value)        # the message names the offending line


# ---- C -----------------------------------------------------------------------------------------

def test_c_basic_declaration():
    tokens = tokenize_c("int x = 0x1F; // hex\n")
    assert kinds_values(tokens) == [("KEYWORD", "int"), ("IDENT", "x"), ("OP", "="), ("NUMBER", "0x1F"),
                                    ("OP", ";"), ("COMMENT", "// hex")]


def test_c_preprocessor_is_one_token_including_continuation():
    tokens = tokenize_c("#define SQUARE(a) \\\n    ((a) * (a))\nint y;\n")
    assert tokens[0].kind == "PREPROC"
    assert "((a) * (a))" in tokens[0].value
    assert kinds_values(tokens[1:]) == [("KEYWORD", "int"), ("IDENT", "y"), ("OP", ";")]


def test_c_strings_chars_and_escapes():
    tokens = tokenize_c('char c = \'\\n\'; char *s = "say \\"hi\\"";')
    assert ("CHAR", "'\\n'") in kinds_values(tokens)
    assert ("STRING", '"say \\"hi\\""') in kinds_values(tokens)


def test_c_longest_match_operators():
    tokens = tokenize_c("a <<= 2; p->q++; b >>= c && d || e != f;")
    ops = [t.value for t in tokens if t.kind == "OP"]
    for expected in ("<<=", "->", "++", ">>=", "&&", "||", "!="):
        assert expected in ops


def test_c_number_forms():
    tokens = tokenize_c("double a = 1.5e-3; float b = 2.0f; long c = 10UL; int d = 0b101; int e = 017;")
    numbers = [t.value for t in tokens if t.kind == "NUMBER"]
    assert numbers == ["1.5e-3", "2.0f", "10UL", "0b101", "017"]


def test_c_block_comment_and_keywords():
    tokens = tokenize_c("/* multi\n line */ while (1) { break; }")
    assert tokens[0].kind == "COMMENT" and tokens[0].end_line == 2
    assert ("KEYWORD", "while") in kinds_values(tokens)
    assert ("KEYWORD", "break") in kinds_values(tokens)


@pytest.mark.parametrize("source", ['char *s = "never closed;\n', "/* no end", "char c = 'x;\n"])
def test_c_unterminated_literals_raise(source):
    with pytest.raises(TokenizeError):
        tokenize_c(source)
