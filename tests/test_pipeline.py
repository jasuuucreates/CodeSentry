"""End-to-end pipeline behaviour (contract section 6)."""
import json

import pytest

from engine import EngineConfig, SourceFile, TokenizeError, analyze_batch, analyze_pair, explain

from .conftest import DATASET

PAIR_KEYS = {"a_id", "b_id", "a_name", "b_name", "language", "scores", "verdict", "matches", "stats", "warnings"}
SCORE_KEYS = {"token", "containment", "structure", "ted", "subtree", "fused", "text_baseline", "tfidf_baseline"}
STAT_KEYS = {"a_tokens", "b_tokens", "a_fingerprints", "b_fingerprints", "shared_fingerprints", "a_nodes",
             "b_nodes", "k_effective", "structure_method"}


def py(id_, text, name=None):
    return SourceFile(id=id_, name=name or f"f{id_}.py", language="python", text=text)


def test_identical_files_score_one(py_program):
    result = analyze_pair(py(1, py_program), py(2, py_program))
    assert result["scores"]["token"] == 1.0
    assert result["scores"]["structure"] == 1.0
    assert result["scores"]["fused"] == 1.0
    assert result["verdict"] == "High"
    assert set(result) == PAIR_KEYS
    assert set(result["scores"]) == SCORE_KEYS
    assert set(result["stats"]) == STAT_KEYS


def test_renamed_copy_has_token_score_one(py_program, py_renamed):
    result = analyze_pair(py(1, py_program), py(2, py_renamed))
    assert result["scores"]["token"] == 1.0
    assert result["scores"]["structure"] == 1.0
    assert result["verdict"] == "High"
    assert result["scores"]["text_baseline"] < 0.6        # the plain text baseline is fooled
    assert result["matches"]


def test_unrelated_programs_score_low(py_program, py_unrelated):
    result = analyze_pair(py(1, py_program), py(2, py_unrelated))
    assert result["scores"]["fused"] < 0.5
    assert result["scores"]["token"] < 0.3
    assert result["verdict"] == "Low"


def test_c_reformatted_copy(c_program):
    reformatted = c_program.replace(") {", ")\n{").replace("/* total value of all items */", "// my sum")
    result = analyze_pair(SourceFile(1, "a.c", "c", c_program), SourceFile(2, "b.c", "c", reformatted))
    assert result["scores"]["token"] == 1.0
    assert result["scores"]["structure"] == 1.0


def test_short_file_rule():
    result = analyze_pair(py(1, "x = 1\n"), py(2, "y = 2\n"))
    assert result["stats"]["k_effective"] == 3
    assert result["scores"]["token"] == 1.0
    tiny = analyze_pair(py(1, "x\n"), py(2, "y\n"))
    assert tiny["scores"]["token"] == 1.0          # one token each, identical symbol lists
    assert tiny["warnings"]


def test_tokenize_error_propagates():
    with pytest.raises(TokenizeError):
        analyze_pair(py(1, "s = 'never closed\n"), py(2, "x = 1\n"))


def test_batch_shape_matrix_and_sorting(py_program, py_renamed, py_unrelated, c_program):
    files = [py(1, py_program, "a.py"), py(2, py_renamed, "b.py"), py(3, py_unrelated, "c.py"),
             SourceFile(4, "d.c", "c", c_program), py(5, "x = (\n", "broken.py")]
    calls = []
    result = analyze_batch(files, EngineConfig(), progress=lambda done, total: calls.append((done, total)))
    assert set(result) == {"files", "pairs", "matrix", "summary", "config"}
    assert [f["name"] for f in result["files"]] == ["a.py", "b.py", "c.py", "d.c", "broken.py"]
    assert result["files"][4]["warnings"]                   # the broken file is listed with a warning
    assert len(result["pairs"]) == 3                       # only the 3 valid Python files are compared
    fused = [p["scores"]["fused"] for p in result["pairs"]]
    assert fused == sorted(fused, reverse=True)
    matrix = result["matrix"]
    assert all(matrix[i][i] == 1.0 for i in range(5))
    assert matrix[0][3] is None and matrix[3][0] is None    # python vs c never compared
    assert matrix[0][4] is None                             # broken file skipped
    assert matrix[0][1] == matrix[1][0] == result["pairs"][0]["scores"]["fused"]
    summary = result["summary"]
    assert summary["files"] == 5 and summary["pairs_compared"] == 3
    assert summary["high"] + summary["moderate"] + summary["low"] == 3
    assert calls[0] == (0, 3) and calls[-1] == (3, 3)


def test_explain_shape_and_caps(py_program, py_renamed):
    result = explain(py_program, py_renamed, "python")
    assert set(result) == {"language", "a", "b", "result"}
    side = result["a"]
    assert set(side) == {"raw_tokens", "normalized", "kgrams", "fingerprints", "skeleton", "counts"}
    assert len(side["raw_tokens"]) <= 80 and len(side["normalized"]) <= 80
    assert len(side["kgrams"]) <= 12 and len(side["fingerprints"]) <= 40
    assert all(len(f["hash"]) == 16 for f in side["fingerprints"])
    assert result["result"]["a_name"] == "Snippet A" and result["result"]["b_name"] == "Snippet B"
    assert side["counts"]["normalized"] >= len(side["normalized"])


def test_demo_batch_planted_pairs_rank_above_honest_pairs():
    folder = DATASET / "demo_batch"
    truth_file = folder / "ground_truth.json"
    if not truth_file.exists():
        pytest.skip("dataset/demo_batch has not been built")
    truth = json.loads(truth_file.read_text(encoding="utf-8"))
    paths = sorted(p for p in folder.iterdir() if p.suffix in (".py", ".c"))
    files = [SourceFile(i + 1, p.name, "python" if p.suffix == ".py" else "c", p.read_text(encoding="utf-8"))
             for i, p in enumerate(paths)]
    result = analyze_batch(files)
    planted = {frozenset((p["a"], p["b"])) for p in truth["planted_pairs"]}
    planted_scores = [p["scores"]["fused"] for p in result["pairs"] if frozenset((p["a_name"], p["b_name"])) in planted]
    honest_scores = [p["scores"]["fused"] for p in result["pairs"]
                     if frozenset((p["a_name"], p["b_name"])) not in planted]
    assert len(planted_scores) == len(planted)
    assert min(planted_scores) > max(honest_scores)
    assert min(planted_scores) >= 0.5 and max(honest_scores) < 0.5
