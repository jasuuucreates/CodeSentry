"""Dataset obfuscator (contract section 9): valid, different, deterministic, behaviour-preserving."""
import ast
import subprocess
import sys

import pytest

from engine import SourceFile, analyze_pair
from engine.tokenizer_c import tokenize_c

from .conftest import DATASET, PROJECT

sys.path.insert(0, str(DATASET))
obfuscator = pytest.importorskip("obfuscator")

KINDS = obfuscator.OBFUSCATION_TYPES


def run(text: str, tmp_path) -> str:
    script = tmp_path / "prog.py"
    script.write_text(text, encoding="utf-8")
    proc = subprocess.run([sys.executable, "-I", str(script)], capture_output=True, text=True, timeout=60,
                          env={"PYTHONHASHSEED": "0", "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


def test_types_match_contract():
    assert KINDS == ("rename", "comments_format", "reorder", "loop_swap", "dead_code", "combined")


@pytest.mark.parametrize("kind", KINDS)
def test_python_variants_valid_different_and_same_output(kind, py_program, tmp_path):
    new, report = obfuscator.obfuscate(py_program, "python", kind, seed=3)
    ast.parse(new)
    assert new != py_program
    assert report["kind"] == kind and report["changes"] > 0 and isinstance(report["details"], list)
    assert run(new, tmp_path) == run(py_program, tmp_path)


@pytest.mark.parametrize("kind", KINDS)
def test_c_variants_parse_without_errors(kind, c_program):
    new, report = obfuscator.obfuscate(c_program, "c", kind, seed=3)
    assert obfuscator.is_valid(new, "c")
    assert new != c_program
    assert report["changes"] > 0


@pytest.mark.parametrize("language", ["python", "c"])
def test_deterministic_for_a_seed(language, py_program, c_program):
    text = py_program if language == "python" else c_program
    assert obfuscator.obfuscate(text, language, "combined", seed=11) == \
        obfuscator.obfuscate(text, language, "combined", seed=11)


def test_python_rename_keeps_builtins_imports_and_main(py_program):
    new, _ = obfuscator.obfuscate(py_program, "python", "rename", seed=1)
    tree = ast.parse(new)
    names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    defs = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    assert {"print", "len", "range", "math"} <= names
    assert "main" in defs and "mean" not in defs and "spread" not in defs
    assert "math.sqrt" in new


def test_c_rename_keeps_fields_main_and_library_calls(c_program):
    new, _ = obfuscator.obfuscate(c_program, "c", "rename", seed=1)
    assert "int main(void)" in new and "printf(" in new
    assert ".count" in new and ".price" in new                 # struct fields untouched
    identifiers = {t.value for t in tokenize_c(new) if t.kind == "IDENT"}
    assert "total_value" not in identifiers and "largest" not in identifiers
    assert '"largest %d\\n"' in new                             # string literals untouched
    # a pure rename is invisible to the token score
    result = analyze_pair(SourceFile(1, "a.c", "c", c_program), SourceFile(2, "b.c", "c", new))
    assert result["scores"]["token"] == 1.0


def test_loop_swap_replaces_counted_for_loops(py_program, c_program):
    new_py, _ = obfuscator.obfuscate(py_program, "python", "loop_swap", seed=1)
    assert "for i in range" not in new_py and "while" in new_py
    new_c, report = obfuscator.obfuscate(c_program, "c", "loop_swap", seed=1)
    assert new_c.count("for (") == 0 and new_c.count("while (") == 3
    assert report["changes"] == 3


def test_c_reorder_adds_prototypes(c_program):
    new, _ = obfuscator.obfuscate(c_program, "c", "reorder", seed=2)
    assert "double total_value(struct item items[], int n);" in new
    assert "int largest(int values[], int n);" in new


def test_comments_format_styles(py_program, c_program):
    new_py, _ = obfuscator.obfuscate(py_program, "python", "comments_format", seed=1)
    assert "# add everything up" not in new_py
    assert "\n  total = 0" in new_py or "\n  " in new_py           # 2-space indentation
    assert not any(line.startswith("    ") and not line.startswith("     ") and line.strip()
                   and line.index(line.strip()) == 4 for line in new_py.splitlines() if "def " in line)
    new_c, _ = obfuscator.obfuscate(c_program, "c", "comments_format", seed=1)
    assert "total value of all items" not in new_c
    assert "int largest(int values[], int n)\n{" in new_c            # K&R became Allman


def test_dead_code_adds_one_uncalled_helper(py_program):
    new, report = obfuscator.obfuscate(py_program, "python", "dead_code", seed=4)
    before = {n.name for n in ast.walk(ast.parse(py_program)) if isinstance(n, ast.FunctionDef)}
    after = {n.name for n in ast.walk(ast.parse(new)) if isinstance(n, ast.FunctionDef)}
    added = after - before
    assert len(added) == 1
    helper = added.pop()
    calls = [n for n in ast.walk(ast.parse(new)) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == helper]
    assert calls == []
    unused = [d for d in report["details"] if d.startswith("unused variable")]
    assert 3 <= len(unused) <= 6


def test_invalid_requests_raise_value_error(py_program):
    with pytest.raises(ValueError):
        obfuscator.obfuscate(py_program, "python", "shuffle_everything")
    with pytest.raises(ValueError):
        obfuscator.obfuscate("def broken(:\n", "python", "rename")
    with pytest.raises(ValueError):
        obfuscator.obfuscate(py_program, "java", "rename")
    with pytest.raises(ValueError):
        obfuscator.obfuscate("x = 1\n", "python", "loop_swap")     # nothing to change


def test_generated_dataset_is_valid_if_built():
    manifest = DATASET / "generated" / "manifest.json"
    if not manifest.exists():
        pytest.skip("dataset has not been built")
    for path in (DATASET / "generated").rglob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"))
    for path in (DATASET / "generated").rglob("*.c"):
        assert obfuscator.is_valid(path.read_text(encoding="utf-8"), "c"), path
    assert PROJECT.exists()
