"""Normalization (contract section 3): names and literals become symbols, comments vanish."""
from engine.normalizer import normalize, symbols
from engine.tokenizer_c import tokenize_c
from engine.tokenizer_python import tokenize_python


def test_python_symbols():
    tokens = normalize(tokenize_python("total = total + 1  # add one\n"), "python")
    assert symbols(tokens) == ["ID", "=", "ID", "+", "NUM"]


def test_python_keywords_and_strings():
    tokens = normalize(tokenize_python("for x in 'abc':\n    pass\n"), "python")
    assert symbols(tokens) == ["for", "ID", "in", "STR", ":", "INDENT", "pass", "DEDENT"]


def test_c_symbols_drop_comments_and_preprocessor():
    source = '#include <stdio.h>\n/* hello */\nint main(void) { printf("%c", \'a\'); return 0; }\n'
    tokens = normalize(tokenize_c(source), "c")
    assert symbols(tokens) == ["int", "ID", "(", "void", ")", "{", "ID", "(", "STR", ",", "CHR", ")", ";",
                               "return", "NUM", ";", "}"]


def test_renaming_does_not_change_symbol_stream(py_program, py_renamed):
    a = symbols(normalize(tokenize_python(py_program), "python"))
    b = symbols(normalize(tokenize_python(py_renamed), "python"))
    assert a == b


def test_formatting_and_comments_do_not_change_symbol_stream():
    a = "int f(int a){return a*2;}"
    b = "/* doubled */\nint f(int a)\n{\n    // twice\n    return a * 2;\n}\n"
    assert symbols(normalize(tokenize_c(a), "c")) == symbols(normalize(tokenize_c(b), "c"))


def test_normalize_keeps_positions_and_returns_new_list():
    raw = tokenize_python("a = 5\n")
    normalized = normalize(raw, "python")
    assert normalized is not raw
    assert [t.kind for t in raw] == ["IDENT", "OP", "NUMBER"]          # input untouched
    assert normalized[0].kind == "ID" and normalized[0].value == "a"
    assert (normalized[2].line, normalized[2].col) == (1, 4)
