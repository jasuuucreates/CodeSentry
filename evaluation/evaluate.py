"""Evaluate CodeSentry against the labelled dataset (docs/ARCHITECTURE_CONTRACT.md, section 10).

    .venv\\Scripts\\python.exe evaluation\\evaluate.py

Think of a driving test for the detector. ``dataset/labels.json`` is the examiner's answer
sheet: for every pair of programs it says whether one was copied from the other (label 1) or
written independently (label 0). Every detection method is shown every pair, gives a similarity
score, and is marked against the answer sheet:

* at the fixed default threshold 0.50 (score >= 0.50 means "flagged as copied"): confusion
  matrix, precision, recall, F1 and accuracy;
* at the threshold in {0.00, 0.01, ..., 1.00} with the best F1 - reported separately because it
  is tuned on the same data it is measured on, so it is an optimistic upper bound;
* ROC AUC with the rank (Mann-Whitney U) formula, ties counted as 0.5: the probability that a
  randomly chosen copied pair scores higher than a randomly chosen independent pair. It does not
  depend on any threshold;
* recall for every obfuscation category and false-positive rate for every negative category at
  0.50, and the mean time per pair.

The five methods: ``text`` (difflib on raw lines), ``tfidf`` (TF-IDF cosine, IDF over every
dataset file of the same language), ``token`` (winnowing Jaccard), ``structure`` (AST tree
similarity) and ``hybrid`` (the fused score the web app shows). All of them are computed with an
explicit ``EngineConfig()`` - the untrained defaults - never with ``engine/trained_config.json``.
Every number in the outputs comes from running this script; nothing is typed in by hand.

Outputs in ``evaluation/results/``: ``evaluation.json``, ``pair_scores.csv``, ``summary.md``.
If ``evaluation/results/training_cv.json`` (written by ``training/train_model.py``) exists, its
methods are merged into ``evaluation.json`` after the five methods computed here.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

from engine.baselines import cosine, text_similarity, tfidf_vectors  # noqa: E402
from engine.fusion import fuse  # noqa: E402
from engine.models import EngineConfig, SourceFile  # noqa: E402
from engine.normalizer import normalize  # noqa: E402
from engine.pipeline import compare_prepared, prepare  # noqa: E402
from engine.structure_c import c_skeleton  # noqa: E402
from engine.structure_python import python_skeleton  # noqa: E402
from engine.tokenizer_c import tokenize_c  # noqa: E402
from engine.tokenizer_python import tokenize_python  # noqa: E402
from engine.tree_similarity import structural_similarity  # noqa: E402
from engine.winnowing import fingerprint, jaccard  # noqa: E402

DATASET = PROJECT / "dataset"
LABELS = DATASET / "labels.json"
RESULTS = PROJECT / "evaluation" / "results"
TRAINING_CV = RESULTS / "training_cv.json"

DEFAULT_THRESHOLD = 0.5
THRESHOLDS = [i / 100 for i in range(101)]
METHOD_ORDER = ["text", "tfidf", "token", "structure", "hybrid"]
METHOD_LABELS = {
    "text": "Plain text matching (difflib, raw lines)",
    "tfidf": "TF-IDF cosine (raw words)",
    "token": "Token winnowing (Jaccard of fingerprints)",
    "structure": "Structure (AST tree similarity)",
    "hybrid": "Hybrid (token + structure)",
}
# Which PairResult score each method is.
SCORE_KEYS = {"text": "text_baseline", "tfidf": "tfidf_baseline", "token": "token",
              "structure": "structure", "hybrid": "fused"}
POSITIVE_CATEGORIES = ["rename", "comments_format", "reorder", "loop_swap", "dead_code", "combined"]
NEGATIVE_CATEGORIES = ["independent_same_problem", "obfuscated_vs_independent", "different_problem"]

_TOKENIZERS = {"python": tokenize_python, "c": tokenize_c}
_SKELETONS = {"python": python_skeleton, "c": c_skeleton}


# ---------------------------------------------------------------------------------------------
# Metrics (pure Python)
# ---------------------------------------------------------------------------------------------

def confusion(scores: list[float], labels: list[int], threshold: float) -> dict:
    """Confusion matrix and the usual ratios; a pair is flagged when score >= threshold."""
    tp = fp = tn = fn = 0
    for score, label in zip(scores, labels):
        flagged = score >= threshold
        if flagged and label == 1:
            tp += 1
        elif flagged:
            fp += 1
        elif label == 1:
            fn += 1
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(scores) if scores else 0.0
    return {"threshold": round(threshold, 2), "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4),
            "accuracy": round(accuracy, 4)}


def best_threshold(scores: list[float], labels: list[int]) -> dict:
    """The threshold in 0.00..1.00 with the highest F1 (ties: the lowest such threshold)."""
    best = None
    for threshold in THRESHOLDS:
        result = confusion(scores, labels, threshold)
        if best is None or result["f1"] > best["f1"]:
            best = result
    return best


def auc_mann_whitney(scores: list[float], labels: list[int]) -> float:
    """ROC AUC = U / (P * N) with U = R_pos - P(P+1)/2, using mid-ranks so ties count 0.5."""
    order = sorted(range(len(scores)), key=lambda i: scores[i])
    ranks = [0.0] * len(scores)
    i = 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and scores[order[j + 1]] == scores[order[i]]:
            j += 1
        mid_rank = (i + j) / 2 + 1          # ranks are 1-based; tied scores share the mean rank
        for k in range(i, j + 1):
            ranks[order[k]] = mid_rank
        i = j + 1
    positives = sum(1 for label in labels if label == 1)
    negatives = len(labels) - positives
    if positives == 0 or negatives == 0:
        return 0.0
    rank_sum = sum(rank for rank, label in zip(ranks, labels) if label == 1)
    u = rank_sum - positives * (positives + 1) / 2
    return round(u / (positives * negatives), 4)


# ---------------------------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------------------------

def load_pairs() -> list[dict]:
    data = json.loads(LABELS.read_text(encoding="utf-8"))
    return data["pairs"]


def language_files(language: str) -> list[str]:
    """Every dataset file of a language (relative to dataset/), the TF-IDF document collection."""
    ext = ".py" if language == "python" else ".c"
    return sorted(p.relative_to(DATASET).as_posix() for p in (DATASET / "generated" / language).rglob(f"*{ext}"))


def score_pairs(pairs: list[dict], config: EngineConfig) -> tuple[list[dict], dict]:
    """Score every labelled pair with the engine; returns (rows, per-method mean ms per pair)."""
    texts: dict[str, str] = {}
    for pair in pairs:
        for key in ("a", "b"):
            if pair[key] not in texts:
                texts[pair[key]] = (DATASET / pair[key]).read_text(encoding="utf-8")
    languages = sorted({pair["language"] for pair in pairs})
    for language in languages:
        for rel in language_files(language):
            texts.setdefault(rel, (DATASET / rel).read_text(encoding="utf-8"))

    # TF-IDF: one IDF per language over all dataset files of that language.
    tfidf_vec: dict[str, dict[str, float]] = {}
    for language in languages:
        names = language_files(language)
        for name, vector in zip(names, tfidf_vectors([texts[n] for n in names])):
            tfidf_vec[name] = vector

    # Scores: exactly what the web app computes (pipeline.compare_prepared) with the default config.
    prepared = {}
    ids = {}
    for name in sorted({p["a"] for p in pairs} | {p["b"] for p in pairs}):
        language = "python" if name.endswith(".py") else "c"
        ids[name] = len(ids) + 1
        prepared[name] = prepare(SourceFile(id=ids[name], name=name, language=language, text=texts[name]), config)
    rows = []
    for pair in pairs:
        tfidf_score = cosine(tfidf_vec[pair["a"]], tfidf_vec[pair["b"]])
        result = compare_prepared(prepared[pair["a"]], prepared[pair["b"]], config, tfidf_score)
        row = dict(pair)
        for method in METHOD_ORDER:
            value = result["scores"][SCORE_KEYS[method]]
            row[method] = 0.0 if value is None else value
        row["structure_method"] = result["stats"]["structure_method"]
        rows.append(row)

    timing = time_methods(pairs, texts, languages, config)
    return rows, timing


def time_methods(pairs: list[dict], texts: dict[str, str], languages: list[str], config: EngineConfig) -> dict:
    """Mean milliseconds per pair for each method, measured in a separate pass per method.

    Each pass starts from the raw source texts. One-off per-file work (TF-IDF vectors, token
    fingerprints, syntax skeletons) is done once per file and its cost is spread over the pairs,
    exactly as a batch run does it.
    """
    n = len(pairs)
    files = sorted({p["a"] for p in pairs} | {p["b"] for p in pairs})
    lang_of = {name: ("python" if name.endswith(".py") else "c") for name in files}
    timing = {}

    started = time.perf_counter()
    for pair in pairs:
        text_similarity(texts[pair["a"]], texts[pair["b"]])
    timing["text"] = (time.perf_counter() - started) * 1000 / n

    started = time.perf_counter()
    vectors = {}
    for language in languages:
        names = language_files(language)
        for name, vector in zip(names, tfidf_vectors([texts[x] for x in names])):
            vectors[name] = vector
    for pair in pairs:
        cosine(vectors[pair["a"]], vectors[pair["b"]])
    timing["tfidf"] = (time.perf_counter() - started) * 1000 / n

    def token_pass():
        normalized = {name: normalize(_TOKENIZERS[lang_of[name]](texts[name]), lang_of[name]) for name in files}
        prints = {name: fingerprint(tokens, config.k, config.w) for name, tokens in normalized.items()}
        out = []
        for pair in pairs:
            ta, tb = normalized[pair["a"]], normalized[pair["b"]]
            shorter = min(len(ta), len(tb))
            k_eff = config.k if shorter >= config.k else max(2, shorter)
            fa = prints[pair["a"]] if k_eff == config.k else fingerprint(ta, k_eff, config.w)
            fb = prints[pair["b"]] if k_eff == config.k else fingerprint(tb, k_eff, config.w)
            out.append(jaccard(fa, fb))
        return out

    def structure_pass():
        skeletons = {name: _SKELETONS[lang_of[name]](texts[name]) for name in files}
        return [structural_similarity(skeletons[p["a"]], skeletons[p["b"]], config.ted_node_cap)["structure"]
                for p in pairs]

    started = time.perf_counter()
    token_scores = token_pass()
    timing["token"] = (time.perf_counter() - started) * 1000 / n

    started = time.perf_counter()
    structure_scores = structure_pass()
    timing["structure"] = (time.perf_counter() - started) * 1000 / n

    started = time.perf_counter()
    token_scores = token_pass()
    structure_scores = structure_pass()
    for token, structure in zip(token_scores, structure_scores):
        fuse(token, structure, config)
    timing["hybrid"] = (time.perf_counter() - started) * 1000 / n
    return {method: round(value, 3) for method, value in timing.items()}


# ---------------------------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------------------------

def evaluate_method(rows: list[dict], method: str, mean_ms: float) -> dict:
    scores = [row[method] for row in rows]
    labels = [row["label"] for row in rows]
    recall_by_category = {}
    for category in POSITIVE_CATEGORIES:
        selected = [row for row in rows if row["category"] == category]
        if selected:
            hits = sum(1 for row in selected if row[method] >= DEFAULT_THRESHOLD)
            recall_by_category[category] = round(hits / len(selected), 4)
    fpr_by_category = {}
    for category in NEGATIVE_CATEGORIES:
        selected = [row for row in rows if row["category"] == category]
        if selected:
            flagged = sum(1 for row in selected if row[method] >= DEFAULT_THRESHOLD)
            fpr_by_category[category] = round(flagged / len(selected), 4)
    return {
        "label": METHOD_LABELS[method],
        "at_default": confusion(scores, labels, DEFAULT_THRESHOLD),
        "best": best_threshold(scores, labels),
        "auc": auc_mann_whitney(scores, labels),
        "mean_ms": mean_ms,
        "recall_by_category": recall_by_category,
        "fpr_by_category": fpr_by_category,
    }


def merge_training(evaluation: dict) -> list[str]:
    """Merge evaluation/results/training_cv.json (if present); returns the merged method names."""
    if not TRAINING_CV.exists():
        return []
    try:
        training = json.loads(TRAINING_CV.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"warning: could not read {TRAINING_CV}: {exc}")
        return []
    merged = []
    for name, entry in (training.get("methods") or {}).items():
        evaluation["methods"][name] = entry
    for name in training.get("method_order") or list((training.get("methods") or {}).keys()):
        if name in evaluation["methods"] and name not in evaluation["method_order"]:
            evaluation["method_order"].append(name)
            merged.append(name)
    return merged


def _fmt(x) -> str:
    return "-" if x is None else f"{x:.3f}"


def write_summary(evaluation: dict, merged: list[str]) -> str:
    ds = evaluation["dataset"]
    lines = [
        "# CodeSentry - evaluation summary",
        "",
        f"Generated {evaluation['generated_at']} by `evaluation/evaluate.py` from `dataset/labels.json`.",
        "Every number below comes from running the script; nothing is entered by hand.",
        "Engine settings: the untrained defaults, `EngineConfig()` "
        f"(k = {evaluation['config']['k']}, w = {evaluation['config']['w']}, "
        f"w_token = {evaluation['config']['w_token']}, w_structure = {evaluation['config']['w_structure']}).",
        "",
        "## Dataset",
        "",
        f"* {ds['pairs']} labelled pairs: {ds['positives']} copied (positive), {ds['negatives']} independent (negative)",
        f"* by language: " + ", ".join(f"{k} {v}" for k, v in ds["by_language"].items()),
        f"* by category: " + ", ".join(f"{k} {v}" for k, v in ds["by_category"].items()),
        "",
        f"## Results at the fixed default threshold {DEFAULT_THRESHOLD:.2f}",
        "",
        "A pair is flagged when its score is >= 0.50.",
        "",
        "| Method | Precision | Recall | F1 | Accuracy | ROC AUC | TP | FP | TN | FN | ms / pair |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name in METHOD_ORDER:
        m = evaluation["methods"][name]
        d = m["at_default"]
        lines.append(f"| {m['label']} | {_fmt(d['precision'])} | {_fmt(d['recall'])} | {_fmt(d['f1'])} | "
                     f"{_fmt(d['accuracy'])} | {_fmt(m['auc'])} | {d['tp']} | {d['fp']} | {d['tn']} | {d['fn']} | "
                     f"{m['mean_ms']:.2f} |")
    lines += [
        "",
        "## Best-F1 threshold (tuned on this same dataset - optimistic)",
        "",
        "The threshold in 0.00, 0.01, ..., 1.00 that maximises F1 for each method. It is chosen on the",
        "data it is measured on, so these figures are an upper bound, not an unbiased estimate.",
        "",
        "| Method | Threshold | Precision | Recall | F1 | Accuracy |",
        "|---|---|---|---|---|---|",
    ]
    for name in METHOD_ORDER:
        m = evaluation["methods"][name]
        b = m["best"]
        lines.append(f"| {m['label']} | {b['threshold']:.2f} | {_fmt(b['precision'])} | {_fmt(b['recall'])} | "
                     f"{_fmt(b['f1'])} | {_fmt(b['accuracy'])} |")
    lines += ["", "## Recall per obfuscation category (threshold 0.50)", "",
              "| Method | " + " | ".join(POSITIVE_CATEGORIES) + " |",
              "|---|" + "---|" * len(POSITIVE_CATEGORIES)]
    for name in METHOD_ORDER:
        m = evaluation["methods"][name]
        lines.append(f"| {name} | " + " | ".join(_fmt(m["recall_by_category"].get(c)) for c in POSITIVE_CATEGORIES)
                     + " |")
    lines += ["", "## False-positive rate per negative category (threshold 0.50)", "",
              "| Method | " + " | ".join(NEGATIVE_CATEGORIES) + " |",
              "|---|" + "---|" * len(NEGATIVE_CATEGORIES)]
    for name in METHOD_ORDER:
        m = evaluation["methods"][name]
        lines.append(f"| {name} | " + " | ".join(_fmt(m["fpr_by_category"].get(c)) for c in NEGATIVE_CATEGORIES)
                     + " |")
    if merged:
        lines += ["", "## Trained models, grouped cross-validation (see training/results/summary.md)", "",
                  "Merged from `evaluation/results/training_cv.json`, written by `training/train_model.py`.",
                  "", "| Method | Precision | Recall | F1 | Accuracy | ROC AUC |", "|---|---|---|---|---|---|"]
        for name in merged:
            m = evaluation["methods"][name]
            d = m.get("at_default") or {}
            lines.append(f"| {m.get('label', name)} | {_fmt(d.get('precision'))} | {_fmt(d.get('recall'))} | "
                         f"{_fmt(d.get('f1'))} | {_fmt(d.get('accuracy'))} | {_fmt(m.get('auc'))} |")
    lines += [
        "",
        "## Notes",
        "",
        "* ROC AUC uses the rank (Mann-Whitney U) formula with ties counted as 0.5.",
        "* ms / pair is the wall time of a full pass over all pairs divided by the number of pairs;",
        "  one-off per-file work (TF-IDF vectors, fingerprints, skeletons) is included in that pass.",
        "* Per-pair scores for every method are in `pair_scores.csv`.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    config = EngineConfig()            # explicit untrained defaults - never engine/trained_config.json
    pairs = load_pairs()
    print(f"Scoring {len(pairs)} labelled pairs with 5 methods ...")
    rows, timing = score_pairs(pairs, config)
    positives = sum(1 for p in pairs if p["label"] == 1)
    evaluation = {
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "dataset": {
            "pairs": len(pairs),
            "positives": positives,
            "negatives": len(pairs) - positives,
            "by_language": dict(sorted(Counter(p["language"] for p in pairs).items())),
            "by_category": {c: n for c in POSITIVE_CATEGORIES + NEGATIVE_CATEGORIES
                            for n in [sum(1 for p in pairs if p["category"] == c)] if n},
        },
        "default_threshold": DEFAULT_THRESHOLD,
        "config": config.to_dict(),
        "methods": {m: evaluate_method(rows, m, timing[m]) for m in METHOD_ORDER},
        "method_order": list(METHOD_ORDER),
    }
    merged = merge_training(evaluation)

    RESULTS.mkdir(parents=True, exist_ok=True)
    (RESULTS / "evaluation.json").write_text(json.dumps(evaluation, indent=2) + "\n", encoding="utf-8")
    with (RESULTS / "pair_scores.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["a", "b", "language", "problem", "category", "label"] + METHOD_ORDER)
        for row in rows:
            writer.writerow([row["a"], row["b"], row["language"], row["problem"], row["category"], row["label"]]
                            + [f"{row[m]:.4f}" for m in METHOD_ORDER])
    (RESULTS / "summary.md").write_text(write_summary(evaluation, merged), encoding="utf-8")

    print(f"{'method':10s} {'prec':>6s} {'rec':>6s} {'f1':>6s} {'acc':>6s} {'auc':>6s} {'best_t':>6s} {'best_f1':>7s} {'ms':>7s}")
    for name in METHOD_ORDER:
        m = evaluation["methods"][name]
        d = m["at_default"]
        print(f"{name:10s} {d['precision']:6.3f} {d['recall']:6.3f} {d['f1']:6.3f} {d['accuracy']:6.3f} "
              f"{m['auc']:6.3f} {m['best']['threshold']:6.2f} {m['best']['f1']:7.3f} {m['mean_ms']:7.2f}")
    if merged:
        print("merged trained methods:", ", ".join(merged))
    print(f"wrote {RESULTS / 'evaluation.json'}, pair_scores.csv, summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
