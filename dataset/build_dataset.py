"""Build the evaluation dataset and the demo batch from the hand-written programs.

    .venv\\Scripts\\python.exe dataset\\build_dataset.py

Idempotent: deletes and recreates its outputs every time (docs/ARCHITECTURE_CONTRACT.md, s. 9):

* ``dataset/generated/<language>/<problem>/`` - ``original``, ``independent_1``, ``independent_2``
  (copies) and ``variant_<type>`` for the six obfuscation types;
* ``dataset/generated/manifest.json`` - every obfuscation report plus the checks that were run;
* ``dataset/labels.json`` - the labelled pairs used by ``evaluation/evaluate.py``;
* ``dataset/demo_batch/`` - the 13-student demo class, ``ground_truth.json`` and ``README.md``.

Every generated file is checked before it is written; nothing invalid is ever written:

* syntax - Python: ``ast.parse``; C: tree-sitter with no ERROR or missing node;
* Python behaviour - the variant is executed with the venv interpreter and its standard output
  must equal the original's (exit code 0 for both). This is direct evidence that the disguise
  did not change what the program does;
* C invariants (no C compiler is assumed) - every string literal is kept; for ``rename`` the
  token stream is identical except for a consistent one-to-one identifier mapping; for
  ``comments_format`` the code tokens are identical; for ``reorder`` the function definitions are
  the same texts; for ``dead_code`` the original token stream is a subsequence of the new one; for
  ``loop_swap`` identifiers and literals are kept with the same counts.

A variant that fails its checks is retried with other seeds and, if it still fails, skipped and
recorded under ``skipped`` in the manifest.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

DATASET = Path(__file__).resolve().parent
PROJECT = DATASET.parent
sys.path.insert(0, str(DATASET))
sys.path.insert(0, str(PROJECT))

import obfuscator  # noqa: E402
from obfuscator import OBFUSCATION_TYPES, obfuscate, is_valid  # noqa: E402

from engine.tokenizer_c import tokenize_c  # noqa: E402

PROBLEMS = DATASET / "problems"
DEMO_SOURCE = DATASET / "demo_source"
GENERATED = DATASET / "generated"
DEMO_BATCH = DATASET / "demo_batch"
LABELS = DATASET / "labels.json"

LANGUAGES = {"python": ".py", "c": ".c"}
SEED_ATTEMPTS = (0, 1000, 2000, 3000, 4000)

_VENV_PYTHON = PROJECT / ".venv" / "Scripts" / "python.exe"
PYTHON = str(_VENV_PYTHON) if _VENV_PYTHON.exists() else sys.executable

_RUN_CACHE: dict[str, tuple[int, str, str]] = {}


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------

def run_python(text: str, workdir: Path) -> tuple[int, str, str]:
    """Run a Python program with the venv interpreter; returns (exit code, stdout, stderr)."""
    if text in _RUN_CACHE:
        return _RUN_CACHE[text]
    workdir.mkdir(parents=True, exist_ok=True)
    script = workdir / "_check_run.py"
    script.write_text(text, encoding="utf-8")
    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8")
    try:
        proc = subprocess.run([PYTHON, "-I", str(script)], capture_output=True, text=True,
                              encoding="utf-8", timeout=60, cwd=str(workdir), env=env)
        result = (proc.returncode, proc.stdout, proc.stderr)
    except subprocess.TimeoutExpired:
        result = (-1, "", "timeout")
    finally:
        script.unlink(missing_ok=True)
    _RUN_CACHE[text] = result
    return result


def _c_tokens(text: str):
    return tokenize_c(text)


def _code_tokens(text: str) -> list[tuple[str, str]]:
    return [(t.kind, t.value) for t in _c_tokens(text) if t.kind not in ("COMMENT", "PREPROC")]


def _is_subsequence(small: list, big: list) -> bool:
    it = iter(big)
    return all(any(x == y for y in it) for x in small)


def c_invariants(original: str, new: str, kind: str) -> list[str]:
    """Static behaviour checks for a C variant; raises ValueError when one fails."""
    passed = []
    orig_tokens = _code_tokens(original)
    new_tokens = _code_tokens(new)
    strings = Counter(v for k, v in orig_tokens if k == "STRING")
    if Counter(v for k, v in new_tokens if k == "STRING") != strings:
        raise ValueError("string literals changed")
    passed.append("string literals unchanged")
    if kind == "rename":
        if len(orig_tokens) != len(new_tokens):
            raise ValueError("token count changed")
        # struct fields (`acc->amount`, `double amount;` inside a struct) are never renamed, even
        # when a parameter of the same spelling is: their positions are taken from tree-sitter
        from obfuscator import _c_parse, _walk  # noqa: PLC0415
        src = original.encode("utf-8")
        field_positions = {(n.start_point[0] + 1, n.start_point[1]) for n in _walk(_c_parse(src).root_node)
                           if n.type == "field_identifier"}
        positions = [(t.line, t.col) for t in _c_tokens(original) if t.kind not in ("COMMENT", "PREPROC")]
        forward: dict[str, str] = {}
        backward: dict[str, str] = {}
        for (k1, v1), (k2, v2), pos in zip(orig_tokens, new_tokens, positions):
            if k1 != k2:
                raise ValueError("token kinds changed")
            if k1 == "IDENT" and pos in field_positions:
                if v1 != v2:
                    raise ValueError(f"struct field {v1} was renamed")
                continue
            if k1 == "IDENT":
                if forward.setdefault(v1, v2) != v2 or backward.setdefault(v2, v1) != v1:
                    raise ValueError("identifier mapping is not one-to-one")
            elif v1 != v2:
                raise ValueError("a non-identifier token changed")
        passed.append("token stream identical up to a one-to-one identifier mapping (struct fields kept)")
    elif kind == "comments_format":
        if orig_tokens != new_tokens:
            raise ValueError("code tokens changed")
        passed.append("code tokens identical (only comments and layout changed)")
    elif kind == "reorder":
        from obfuscator import _c_parse, _walk  # noqa: PLC0415
        def functions(text):
            src = text.encode("utf-8")
            return sorted(src[n.start_byte:n.end_byte].decode() for n in _walk(_c_parse(src).root_node)
                          if n.type == "function_definition")
        if functions(original) != functions(new):
            raise ValueError("function definitions changed")
        passed.append("function definitions identical, only their order changed (+ prototypes)")
    elif kind == "dead_code":
        if not _is_subsequence(orig_tokens, new_tokens):
            raise ValueError("original tokens are not preserved")
        passed.append("original token stream is a subsequence of the variant (insertions only)")
    elif kind == "loop_swap":
        def literals(tokens):
            return Counter((k, v) for k, v in tokens if k in ("IDENT", "NUMBER", "STRING", "CHAR"))
        if literals(orig_tokens) != literals(new_tokens):
            raise ValueError("identifiers or literals changed")
        fors = sum(1 for k, v in orig_tokens if v == "for") - sum(1 for k, v in new_tokens if v == "for")
        whiles = sum(1 for k, v in new_tokens if v == "while") - sum(1 for k, v in orig_tokens if v == "while")
        if fors <= 0 or fors != whiles:
            raise ValueError("for/while counts inconsistent")
        passed.append(f"identifiers and literals kept; {fors} for loop(s) became while loop(s)")
    return passed


def make_variant(text: str, language: str, kind: str, base_seed: int, workdir: Path,
                 reference_output: tuple[int, str, str] | None) -> tuple[str, dict, int, dict]:
    """Obfuscate and check; tries several seeds. Raises ValueError if every attempt fails."""
    errors = []
    for offset in SEED_ATTEMPTS:
        seed = base_seed + offset
        try:
            new, report = obfuscate(text, language, kind, seed)
            if not is_valid(new, language):
                raise ValueError("not syntactically valid")
            checks = {"syntax": "ok"}
            if language == "python":
                code, out, err = run_python(new, workdir)
                if code != 0:
                    raise ValueError(f"variant exits with code {code}: {err.strip()[-300:]}")
                if reference_output is not None and out != reference_output[1]:
                    raise ValueError("stdout differs from the original's")
                checks["run_equivalent"] = True
                checks["stdout_lines"] = len(out.splitlines())
            else:
                checks["invariants"] = c_invariants(text, new, kind)
            return new, report, seed, checks
        except ValueError as exc:
            errors.append(f"seed {seed}: {exc}")
    raise ValueError("; ".join(errors))


# ---------------------------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------------------------

def _rel(path: Path) -> str:
    return path.relative_to(DATASET).as_posix()


def _reset(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def build_generated(manifest: dict, workdir: Path) -> dict:
    """Write dataset/generated/ and return {(language, problem): {name: path}}."""
    _reset(GENERATED)
    layout: dict = {}
    problems = sorted(p for p in PROBLEMS.iterdir() if p.is_dir())
    for p_index, problem_dir in enumerate(problems):
        problem = problem_dir.name
        for language, ext in LANGUAGES.items():
            out_dir = GENERATED / language / problem
            out_dir.mkdir(parents=True, exist_ok=True)
            files = {}
            for name in ("original", "independent_1", "independent_2"):
                source = problem_dir / f"{name}{ext}"
                text = source.read_text(encoding="utf-8")
                if not is_valid(text, language):
                    raise SystemExit(f"{source} is not valid {language}")
                target = out_dir / f"{name}{ext}"
                target.write_text(text, encoding="utf-8", newline="\n")
                files[name] = target
            original = files["original"].read_text(encoding="utf-8")
            reference = None
            if language == "python":
                reference = run_python(original, workdir)
                if reference[0] != 0:
                    raise SystemExit(f"{problem}/original.py does not run: {reference[2]}")
            for k_index, kind in enumerate(OBFUSCATION_TYPES):
                base_seed = (p_index + 1) * 100 + k_index * 10 + (0 if language == "python" else 5)
                target = out_dir / f"variant_{kind}{ext}"
                entry = {"language": language, "problem": problem, "kind": kind,
                         "source": _rel(files["original"]), "path": _rel(target)}
                try:
                    new, report, seed, checks = make_variant(original, language, kind, base_seed,
                                                             workdir, reference)
                except ValueError as exc:
                    entry["reason"] = str(exc)
                    manifest["skipped"].append(entry)
                    print(f"  SKIPPED {language} {problem} {kind}: {exc}")
                    continue
                target.write_text(new, encoding="utf-8", newline="\n")
                entry.update({"seed": seed, "report": report, "checks": checks})
                manifest["variants"].append(entry)
                files[f"variant_{kind}"] = target
            layout[(language, problem)] = files
            print(f"  {language:6s} {problem}: {sum(1 for k in files if k.startswith('variant_'))} variants")
    return layout


def build_labels(layout: dict) -> dict:
    pairs = []
    for (language, problem), files in sorted(layout.items()):
        original = files["original"]
        for kind in OBFUSCATION_TYPES:
            variant = files.get(f"variant_{kind}")
            if variant is not None:
                pairs.append({"a": _rel(original), "b": _rel(variant), "label": 1, "language": language,
                              "problem": problem, "category": kind})
        for a, b in (("original", "independent_1"), ("original", "independent_2"),
                     ("independent_1", "independent_2")):
            pairs.append({"a": _rel(files[a]), "b": _rel(files[b]), "label": 0, "language": language,
                          "problem": problem, "category": "independent_same_problem"})
        combined = files.get("variant_combined")
        if combined is not None:
            pairs.append({"a": _rel(combined), "b": _rel(files["independent_1"]), "label": 0,
                          "language": language, "problem": problem, "category": "obfuscated_vs_independent"})
    for language in LANGUAGES:
        problems = sorted(problem for (lang, problem) in layout if lang == language)
        for i, p in enumerate(problems):
            for q in problems[i + 1:]:
                pairs.append({"a": _rel(layout[(language, p)]["original"]),
                              "b": _rel(layout[(language, q)]["original"]), "label": 0,
                              "language": language, "problem": f"{p}|{q}", "category": "different_problem"})
    return {"version": 1, "pairs": pairs}


DEMO_PLAN = [
    # (student file, source, transform chain applied in order)
    ("student_01.py", "honest_01.py", []),
    ("student_02.py", "honest_02.py", []),
    ("student_03.py", "honest_03.py", []),
    ("student_04.py", "honest_04.py", []),
    ("student_05.py", "honest_05.py", []),
    ("student_06.py", "honest_06.py", []),
    ("student_07.py", "honest_07.py", []),
    ("student_08.py", "honest_02.py", ["rename"]),
    ("student_09.py", "honest_05.py", ["combined"]),
    ("student_10.py", "student_09.py", ["comments_format"]),
    ("student_11.py", "honest_07.py", ["reorder", "dead_code"]),
    ("student_12.c", "honest_c_01.c", []),
    ("student_13.c", "honest_c_01.c", ["loop_swap"]),
]

DEMO_PLANTED = [
    {"a": "student_02.py", "b": "student_08.py", "relation": "student_08 = rename(student_02)",
     "expected": "copied"},
    {"a": "student_05.py", "b": "student_09.py",
     "relation": "student_09 = combined(student_05): rename, loop swap, reorder, dead code, comments/format",
     "expected": "copied"},
    {"a": "student_09.py", "b": "student_10.py", "relation": "student_10 = comments_format(student_09)",
     "expected": "copied"},
    {"a": "student_05.py", "b": "student_10.py", "relation": "student_10 = comments_format(combined(student_05))",
     "expected": "copied"},
    {"a": "student_07.py", "b": "student_11.py", "relation": "student_11 = dead_code(reorder(student_07))",
     "expected": "copied"},
    {"a": "student_12.c", "b": "student_13.c", "relation": "student_13 = loop_swap(student_12)",
     "expected": "copied"},
]


def build_demo(manifest: dict, workdir: Path) -> None:
    _reset(DEMO_BATCH)
    produced: dict[str, str] = {}
    entries = []
    for index, (target, source, chain) in enumerate(DEMO_PLAN):
        language = "python" if target.endswith(".py") else "c"
        if source.startswith("student_"):
            text = produced[source]
        else:
            text = (DEMO_SOURCE / source).read_text(encoding="utf-8")
        if not is_valid(text, language):
            raise SystemExit(f"demo source {source} is not valid {language}")
        reference = run_python(text, workdir) if language == "python" else None
        if reference is not None and reference[0] != 0:
            raise SystemExit(f"demo source {source} does not run: {reference[2]}")
        reports = []
        current = text
        for step_index, kind in enumerate(chain):
            base_seed = 7000 + index * 10 + step_index
            current, report, seed, checks = make_variant(current, language, kind, base_seed, workdir, reference)
            reports.append({"kind": kind, "seed": seed, "report": report, "checks": checks})
        (DEMO_BATCH / target).write_text(current, encoding="utf-8", newline="\n")
        produced[target] = current
        entries.append({"file": target, "source": source, "transforms": chain, "steps": reports})
    manifest["demo_batch"] = entries

    copied_files = sorted({p["a"] for p in DEMO_PLANTED} | {p["b"] for p in DEMO_PLANTED})
    ground_truth = {
        "assignment": "Assignment 3 - Student Grade Statistics",
        "files": [{"file": e["file"],
                   "origin": e["source"] if not e["transforms"] else f"{' -> '.join(e['transforms'])} of {e['source']}",
                   "honest": not e["transforms"]} for e in entries],
        "planted_pairs": DEMO_PLANTED,
        "involved_in_copying": copied_files,
        "note": "Every same-language pair not listed in planted_pairs is two independent honest solutions.",
    }
    (DEMO_BATCH / "ground_truth.json").write_text(json.dumps(ground_truth, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Demo batch - Assignment 3: Student Grade Statistics",
        "",
        "Thirteen submissions for one class assignment (11 Python, 2 C). Generated by",
        "`dataset/build_dataset.py` from `dataset/demo_source/`; do not edit by hand.",
        "",
        "Honest, independently written solutions: `student_01.py` ... `student_07.py` and `student_12.c`.",
        "",
        "Planted copies (the detector should flag these pairs):",
        "",
        "| Pair | How the copy was disguised |",
        "|---|---|",
    ]
    for planted in DEMO_PLANTED:
        lines.append(f"| `{planted['a']}` - `{planted['b']}` | {planted['relation']} |")
    lines += [
        "",
        "All other same-language pairs are independent solutions and should score low.",
        "Python and C files are never compared with each other.",
        "Every Python copy was executed and prints exactly the same output as its source.",
        "The full machine-readable truth is in `ground_truth.json`.",
        "",
    ]
    (DEMO_BATCH / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    workdir = DATASET / ".build_tmp"
    _reset(workdir)
    manifest = {"version": 1, "obfuscation_types": list(OBFUSCATION_TYPES), "python": PYTHON,
                "checks": {"python": "ast.parse + executed, stdout equal to the original",
                           "c": "tree-sitter without ERROR/missing nodes + static invariants"},
                "variants": [], "skipped": [], "demo_batch": []}
    try:
        print("Generating obfuscated variants ...")
        layout = build_generated(manifest, workdir)
        labels = build_labels(layout)
        LABELS.write_text(json.dumps(labels, indent=2) + "\n", encoding="utf-8")
        print("Building demo batch ...")
        build_demo(manifest, workdir)
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    by_category = Counter(p["category"] for p in labels["pairs"])
    manifest["counts"] = {
        "variants_written": len(manifest["variants"]),
        "variants_skipped": len(manifest["skipped"]),
        "label_pairs": len(labels["pairs"]),
        "positives": sum(1 for p in labels["pairs"] if p["label"] == 1),
        "negatives": sum(1 for p in labels["pairs"] if p["label"] == 0),
        "by_category": dict(sorted(by_category.items())),
    }
    (GENERATED / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest["counts"], indent=2))
    if manifest["skipped"]:
        print(f"{len(manifest['skipped'])} variant(s) skipped - see generated/manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
