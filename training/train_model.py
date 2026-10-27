"""Train CodeSentry's decision layer on the labelled obfuscation dataset.

The detection engine turns a pair of programs into similarity scores; this script learns how to
turn those scores into a decision. Two learners are trained on pair-level features:

1. Calibrated hybrid - keeps the engine's explainable formula
       fused = w * token + (1 - w) * structure
   and learns the weight w and the decision threshold by grid search (maximum F1).
2. Logistic regression - learns a weighted combination of eight similarity features
   (token Jaccard, containment, structure, tree edit distance, subtree overlap, plain-text
   ratio, TF-IDF cosine, length ratio), written in plain Python with gradient descent.

Both are evaluated with GROUPED 5-fold cross-validation: the ten assignment problems are split
into five folds of two problems. A pair is only ever scored by a model that never saw any
program of that pair's problem during training, so an original and its obfuscated variants can
never sit on both sides of the split (no leakage). The untrained baselines are scored on the
same held-out pairs for a fair comparison. Finally both learners are fitted on all pairs and
saved for the web app:

    engine/trained_config.json   learned fusion weights + verdict thresholds (used by the API)
    engine/trained_model.json    logistic regression coefficients

Run from the project root:  .venv\\Scripts\\python.exe training\\train_model.py
"""
from __future__ import annotations

import csv
import json
import math
import random
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from engine import EngineConfig, SourceFile  # noqa: E402
from engine.baselines import cosine, text_similarity, tfidf_vectors  # noqa: E402
from engine.fusion import fuse  # noqa: E402
from engine.pipeline import compare_prepared, prepare  # noqa: E402

DATASET = ROOT / "dataset"
OUT = ROOT / "training" / "results"
EVAL_OUT = ROOT / "evaluation" / "results"

FEATURES = ["token", "containment", "structure", "ted", "subtree", "text", "tfidf", "length_ratio"]
N_FOLDS = 5
HIGH_SHARE = 0.95           # "High" verdict = the score that this share of known copies reach
W_GRID = [round(i * 0.05, 2) for i in range(21)]
T_GRID = [round(i * 0.01, 2) for i in range(101)]


# ---------------------------------------------------------------------------------------------
# Features
# ---------------------------------------------------------------------------------------------

def problem_of(rel_path: str) -> str:
    """'generated/python/p01_grade_statistics/original.py' -> 'p01_grade_statistics'."""
    parts = Path(rel_path).parts
    return parts[2] if len(parts) > 3 else parts[-2]


def build_features(pairs: list[dict]) -> tuple[list[dict], float]:
    """Run the real engine on every labelled pair and collect the similarity features."""
    config = EngineConfig()  # untrained defaults: the features must not depend on the training
    paths = sorted({p["a"] for p in pairs} | {p["b"] for p in pairs})
    texts = {rel: (DATASET / rel).read_text(encoding="utf-8") for rel in paths}
    langs = {}
    for p in pairs:
        langs[p["a"]] = p["language"]
        langs[p["b"]] = p["language"]

    # TF-IDF with the IDF computed over all dataset files of the same language (as evaluate.py).
    tfidf: dict[str, dict[str, float]] = {}
    for lang in sorted(set(langs.values())):
        group = [rel for rel in paths if langs[rel] == lang]
        for rel, vec in zip(group, tfidf_vectors([texts[rel] for rel in group])):
            tfidf[rel] = vec

    prepared = {}
    for i, rel in enumerate(paths):
        prepared[rel] = prepare(SourceFile(id=i + 1, name=Path(rel).name, language=langs[rel],
                                           text=texts[rel]), config)

    rows = []
    start = time.perf_counter()
    for p in pairs:
        pa, pb = prepared[p["a"]], prepared[p["b"]]
        res = compare_prepared(pa, pb, config, tfidf_score=cosine(tfidf[p["a"]], tfidf[p["b"]]))
        s = res["scores"]
        token = s["token"]
        structure = s["structure"] if s["structure"] is not None else token
        len_a, len_b = len(pa.tokens), len(pb.tokens)
        rows.append({
            "a": p["a"], "b": p["b"], "label": int(p["label"]), "language": p["language"],
            "category": p["category"],
            "problem_a": problem_of(p["a"]), "problem_b": problem_of(p["b"]),
            "token": token,
            "containment": s["containment"],
            "structure": structure,
            "ted": s["ted"] if s["ted"] is not None else structure,
            "subtree": s["subtree"] if s["subtree"] is not None else structure,
            "text": text_similarity(texts[p["a"]], texts[p["b"]]),
            "tfidf": s["tfidf_baseline"],
            "length_ratio": (min(len_a, len_b) / max(len_a, len_b)) if max(len_a, len_b) else 0.0,
            "fused_default": s["fused"],
        })
    ms_per_pair = (time.perf_counter() - start) * 1000 / max(1, len(pairs))
    return rows, ms_per_pair


# ---------------------------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------------------------

def confusion(labels: list[int], preds: list[int]) -> dict:
    tp = sum(1 for y, p in zip(labels, preds) if y == 1 and p == 1)
    fp = sum(1 for y, p in zip(labels, preds) if y == 0 and p == 1)
    tn = sum(1 for y, p in zip(labels, preds) if y == 0 and p == 0)
    fn = sum(1 for y, p in zip(labels, preds) if y == 1 and p == 0)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / len(labels) if labels else 0.0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4), "accuracy": round(accuracy, 4)}


def auc(labels: list[int], scores: list[float]) -> float:
    """ROC AUC by the rank (Mann-Whitney U) formula; ties count 0.5."""
    pos = [s for s, y in zip(scores, labels) if y == 1]
    neg = [s for s, y in zip(scores, labels) if y == 0]
    if not pos or not neg:
        return 0.0
    wins = sum((1.0 if p > n else 0.5 if p == n else 0.0) for p in pos for n in neg)
    return round(wins / (len(pos) * len(neg)), 4)


def by_category(rows: list[dict], preds: list[int]) -> tuple[dict, dict]:
    recall_cat, fpr_cat = {}, {}
    cats = sorted({r["category"] for r in rows})
    for cat in cats:
        idx = [i for i, r in enumerate(rows) if r["category"] == cat]
        hits = sum(preds[i] for i in idx)
        if rows[idx[0]]["label"] == 1:
            recall_cat[cat] = round(hits / len(idx), 4)
        else:
            fpr_cat[cat] = round(hits / len(idx), 4)
    return recall_cat, fpr_cat


# ---------------------------------------------------------------------------------------------
# Learner 1: calibrated hybrid (grid search over the engine's own fusion formula)
# ---------------------------------------------------------------------------------------------

def fused_score(row: dict, w: float) -> float:
    cfg = EngineConfig(w_token=w, w_structure=round(1 - w, 2)) if 0 < w < 1 else None
    if cfg is None:  # EngineConfig needs a positive total weight; handle the extremes directly
        return row["token"] if w >= 1 else row["structure"]
    return fuse(row["token"], row["structure"], cfg)


def fit_calibrated(rows: list[dict]) -> dict:
    """Grid search of (w_token, threshold): best F1 first, then the widest margin.

    When many boundaries are equally accurate, the one farthest from the nearest pair - the
    middle of the widest gap between honest pairs and copies - is the most robust choice
    (a one-dimensional maximum-margin rule). Remaining ties prefer balanced weights.
    """
    labels = [r["label"] for r in rows]
    best = None
    for w in W_GRID:
        scores = [fused_score(r, w) for r in rows]
        for t in T_GRID:
            f1 = confusion(labels, [1 if s >= t else 0 for s in scores])["f1"]
            margin = min(abs(s - t) for s in scores)
            key = (f1, round(margin, 4), -abs(w - 0.5), -abs(t - 0.5))
            if best is None or key > best[0]:
                best = (key, w, t)
    return {"w_token": best[1], "threshold": best[2], "train_f1": best[0][0], "margin": best[0][1]}


# ---------------------------------------------------------------------------------------------
# Learner 2: logistic regression (plain Python, batch gradient descent, L2, balanced classes)
# ---------------------------------------------------------------------------------------------

def fit_logreg(rows: list[dict], l2: float = 0.01, lr: float = 0.5, iters: int = 3000) -> dict:
    X = [[r[f] for f in FEATURES] for r in rows]
    y = [r["label"] for r in rows]
    n, d = len(X), len(FEATURES)
    means = [statistics.fmean(col) for col in zip(*X)]
    stds = [statistics.pstdev(col) or 1.0 for col in zip(*X)]
    Z = [[(x[j] - means[j]) / stds[j] for j in range(d)] for x in X]
    n_pos = sum(y)
    n_neg = n - n_pos
    sw = [n / (2 * n_pos) if yi == 1 else n / (2 * n_neg) for yi in y]
    w = [0.0] * d
    b = 0.0
    for _ in range(iters):
        gw = [0.0] * d
        gb = 0.0
        for zi, yi, si in zip(Z, y, sw):
            m = b + sum(wj * zj for wj, zj in zip(w, zi))
            p = 1 / (1 + math.exp(-m)) if m >= 0 else math.exp(m) / (1 + math.exp(m))
            g = si * (p - yi)
            gb += g
            for j in range(d):
                gw[j] += g * zi[j]
        w = [wj - lr * (gj / n + l2 * wj) for wj, gj in zip(w, gw)]
        b -= lr * gb / n
    return {"features": FEATURES, "means": means, "stds": stds, "weights": w, "bias": b,
            "threshold": 0.5}


def predict_logreg(model: dict, row: dict) -> float:
    m = model["bias"] + sum(
        wj * (row[f] - mu) / sd
        for wj, f, mu, sd in zip(model["weights"], model["features"], model["means"], model["stds"]))
    return 1 / (1 + math.exp(-m)) if m >= 0 else math.exp(m) / (1 + math.exp(m))


# ---------------------------------------------------------------------------------------------
# Grouped cross-validation
# ---------------------------------------------------------------------------------------------

def make_folds(rows: list[dict]) -> list[list[str]]:
    problems = sorted({r["problem_a"] for r in rows} | {r["problem_b"] for r in rows})
    size = max(1, math.ceil(len(problems) / N_FOLDS))
    return [problems[i:i + size] for i in range(0, len(problems), size)]


def cross_validate(rows: list[dict]) -> dict:
    """Every pair is tested exactly once: in the fold that holds the problem of its file A.

    The training part of a fold contains only pairs whose two files both come from problems
    outside the test fold, so no program of a test problem is ever seen during training.
    """
    folds = make_folds(rows)
    held = {"calibrated": [None] * len(rows), "calibrated_score": [None] * len(rows),
            "logreg": [None] * len(rows), "logreg_score": [None] * len(rows)}
    per_fold = []
    for k, test_problems in enumerate(folds):
        test_set = set(test_problems)
        test_idx = [i for i, r in enumerate(rows) if r["problem_a"] in test_set]
        train = [r for r in rows if r["problem_a"] not in test_set and r["problem_b"] not in test_set]
        cal = fit_calibrated(train)
        lr_model = fit_logreg(train)
        for i in test_idx:
            s = fused_score(rows[i], cal["w_token"])
            held["calibrated_score"][i] = s
            held["calibrated"][i] = 1 if s >= cal["threshold"] else 0
            p = predict_logreg(lr_model, rows[i])
            held["logreg_score"][i] = p
            held["logreg"][i] = 1 if p >= 0.5 else 0
        labels = [rows[i]["label"] for i in test_idx]
        per_fold.append({
            "fold": k + 1, "test_problems": test_problems, "train_pairs": len(train),
            "test_pairs": len(test_idx), "learned_w_token": cal["w_token"],
            "learned_threshold": cal["threshold"],
            "calibrated_f1": confusion(labels, [held["calibrated"][i] for i in test_idx])["f1"],
            "logreg_f1": confusion(labels, [held["logreg"][i] for i in test_idx])["f1"],
        })
    return {"folds": per_fold, "held": held}


def method_entry(label: str, rows: list[dict], preds: list[int], scores: list[float],
                 threshold: float, mean_ms: float, cv: dict | None = None) -> dict:
    labels = [r["label"] for r in rows]
    at = {"threshold": threshold, **confusion(labels, preds)}
    recall_cat, fpr_cat = by_category(rows, preds)
    entry = {"label": label, "at_default": at, "best": dict(at), "auc": auc(labels, scores),
             "mean_ms": round(mean_ms, 3), "recall_by_category": recall_cat,
             "fpr_by_category": fpr_cat}
    if cv is not None:
        entry["cv"] = cv
    return entry


# ---------------------------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------------------------

def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    global OUT, EVAL_OUT
    args = sys.argv[1:]
    labels_file = Path(args[args.index("--labels") + 1]) if "--labels" in args else DATASET / "labels.json"
    model_dir = ROOT / "engine"
    if "--dry-run" in args:
        # Smoke test: write every output under training/results/dry_run, touch nothing the app reads.
        OUT = EVAL_OUT = model_dir = ROOT / "training" / "results" / "dry_run"
    if not labels_file.exists():
        sys.exit("dataset/labels.json not found - run dataset/build_dataset.py first")
    pairs = json.loads(labels_file.read_text(encoding="utf-8"))["pairs"]
    OUT.mkdir(parents=True, exist_ok=True)
    EVAL_OUT.mkdir(parents=True, exist_ok=True)
    random.seed(0)

    t0 = time.perf_counter()
    rows, ms_per_pair = build_features(pairs)
    print(f"features: {len(rows)} pairs ({sum(r['label'] for r in rows)} positive) "
          f"in {time.perf_counter() - t0:.1f}s, {ms_per_pair:.2f} ms/pair")

    with open(OUT / "features.csv", "w", newline="", encoding="utf-8") as fh:
        cols = ["a", "b", "label", "language", "category", "problem_a", "problem_b"] + FEATURES + ["fused_default"]
        writer = csv.DictWriter(fh, fieldnames=cols)
        writer.writeheader()
        for r in rows:
            writer.writerow({c: (round(r[c], 4) if isinstance(r[c], float) else r[c]) for c in cols})

    cv = cross_validate(rows)
    held = cv["held"]
    folds = cv["folds"]
    f1_cal = [f["calibrated_f1"] for f in folds]
    f1_lr = [f["logreg_f1"] for f in folds]
    mean_t = round(statistics.fmean(f["learned_threshold"] for f in folds), 2)

    labels = [r["label"] for r in rows]
    comparison = {}
    for key, title, col in [("text", "Plain text", "text"), ("tfidf", "TF-IDF cosine", "tfidf"),
                            ("token", "Token winnowing", "token"),
                            ("structure", "AST structure", "structure"),
                            ("hybrid", "Hybrid (default weights)", "fused_default")]:
        scores = [r[col] for r in rows]
        preds = [1 if s >= 0.5 else 0 for s in scores]
        comparison[key] = {"label": title, **confusion(labels, preds), "auc": auc(labels, scores)}
    comparison["hybrid_calibrated"] = {"label": "Calibrated hybrid (trained, CV)",
                                       **confusion(labels, held["calibrated"]),
                                       "auc": auc(labels, held["calibrated_score"])}
    comparison["logreg"] = {"label": "Logistic regression (trained, CV)",
                            **confusion(labels, held["logreg"]),
                            "auc": auc(labels, held["logreg_score"])}

    # ---- final models on all data, saved for the web app ------------------------------------
    final_cal = fit_calibrated(rows)
    w_final = final_cal["w_token"]
    t_mod = final_cal["threshold"]
    all_scores = [fused_score(r, w_final) for r in rows]
    # "High" = at least as similar as HIGH_SHARE of the known disguised copies; between the learned
    # boundary and that score a pair is "Moderate" (flagged, but weaker than typical copies).
    pos_scores = sorted(s for s, y in zip(all_scores, labels) if y == 1)
    t_high = math.floor(pos_scores[int((1 - HIGH_SHARE) * len(pos_scores))] * 100) / 100 if pos_scores else 0.75
    t_high = round(min(max(t_high, t_mod + 0.05), 0.95), 2)
    # EngineConfig needs a positive total weight; keep both evidence sources in the formula
    w_token = min(max(w_final, 0.05), 0.95)
    trained_config = {
        "k": 5, "w": 4,
        "w_token": round(w_token, 2), "w_structure": round(1 - w_token, 2),
        "moderate_threshold": t_mod, "high_threshold": t_high,
        "meta": {
            "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "method": "grid search of fusion weight and threshold on all labelled pairs: "
                      "maximum F1, then maximum margin",
            "pairs": len(rows), "positives": sum(labels),
            "margin": final_cal["margin"],
            "cv_f1_mean": round(statistics.fmean(f1_cal), 4),
            "cv_f1_std": round(statistics.pstdev(f1_cal), 4),
            "moderate_threshold_rule": "learned decision boundary (middle of the widest gap)",
            "high_threshold_rule": f"score reached by {HIGH_SHARE:.0%} of the known plagiarised pairs",
        },
    }
    final_lr = fit_logreg(rows)
    final_lr["meta"] = {"trained_at": trained_config["meta"]["trained_at"], "pairs": len(rows),
                        "cv_f1_mean": round(statistics.fmean(f1_lr), 4),
                        "cv_f1_std": round(statistics.pstdev(f1_lr), 4)}
    (model_dir / "trained_config.json").write_text(json.dumps(trained_config, indent=2), encoding="utf-8")
    (model_dir / "trained_model.json").write_text(json.dumps(final_lr, indent=2), encoding="utf-8")

    # ---- evaluation-page entries (same shape as evaluation.json methods) -----------------
    methods = {
        "hybrid_calibrated": method_entry(
            "Calibrated hybrid (trained, 5-fold grouped CV)", rows, held["calibrated"],
            held["calibrated_score"], mean_t, ms_per_pair,
            {"folds": N_FOLDS, "f1_per_fold": f1_cal, "f1_mean": round(statistics.fmean(f1_cal), 4),
             "f1_std": round(statistics.pstdev(f1_cal), 4)}),
        "logreg": method_entry(
            "Logistic regression (trained, 5-fold grouped CV)", rows, held["logreg"],
            held["logreg_score"], 0.5, ms_per_pair,
            {"folds": N_FOLDS, "f1_per_fold": f1_lr, "f1_mean": round(statistics.fmean(f1_lr), 4),
             "f1_std": round(statistics.pstdev(f1_lr), 4)}),
    }
    training_cv = {"generated_at": trained_config["meta"]["trained_at"], "methods": methods,
                   "method_order": ["hybrid_calibrated", "logreg"]}
    (EVAL_OUT / "training_cv.json").write_text(json.dumps(training_cv, indent=2), encoding="utf-8")

    eval_file = EVAL_OUT / "evaluation.json"
    if eval_file.exists():
        data = json.loads(eval_file.read_text(encoding="utf-8"))
        data.setdefault("methods", {}).update(methods)
        order = data.setdefault("method_order", [])
        for key in training_cv["method_order"]:
            if key not in order:
                order.append(key)
        eval_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    report = {"generated_at": trained_config["meta"]["trained_at"], "pairs": len(rows),
              "positives": sum(labels), "negatives": len(labels) - sum(labels),
              "features": FEATURES, "folds": folds, "comparison_on_held_out_pairs": comparison,
              "trained_config": trained_config, "logistic_regression": final_lr}
    (OUT / "training_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    # ---- human-readable summary ------------------------------------------------------------
    lines = ["# CodeSentry - training results", "",
             f"Generated {report['generated_at']} from `dataset/labels.json`: {len(rows)} labelled pairs "
             f"({sum(labels)} plagiarised, {len(labels) - sum(labels)} not).", "",
             "Validation: grouped 5-fold cross-validation by assignment problem (2 problems per fold); "
             "every pair below is scored by a model that never saw its problem during training.", "",
             "| Method | Precision | Recall | F1 | Accuracy | AUC |", "|---|---|---|---|---|---|"]
    for key, c in comparison.items():
        lines.append(f"| {c['label']} | {c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} | "
                     f"{c['accuracy']:.3f} | {c['auc']:.3f} |")
    lines += ["", "Untrained methods use the fixed threshold 0.50.", "",
              "## Per fold", "", "| Fold | Test problems | Train pairs | Test pairs | Learned w_token | "
              "Learned threshold | Calibrated F1 | LogReg F1 |", "|---|---|---|---|---|---|---|---|"]
    for f in folds:
        lines.append(f"| {f['fold']} | {', '.join(f['test_problems'])} | {f['train_pairs']} | {f['test_pairs']} | "
                     f"{f['learned_w_token']:.2f} | {f['learned_threshold']:.2f} | {f['calibrated_f1']:.3f} | "
                     f"{f['logreg_f1']:.3f} |")
    lines += ["", "## Final trained settings used by the web app (`engine/trained_config.json`)", "",
              f"* w_token = {trained_config['w_token']}, w_structure = {trained_config['w_structure']}",
              f"* Moderate verdict from score {t_mod:.2f} (learned boundary, margin {final_cal['margin']:.3f}), "
              f"High verdict from score {t_high:.2f} (reached by {HIGH_SHARE:.0%} of the known copies)", "",
              "## Logistic regression coefficients (standardised features)", "",
              "| Feature | Weight |", "|---|---|"]
    for f, wv in sorted(zip(FEATURES, final_lr["weights"]), key=lambda x: -abs(x[1])):
        lines.append(f"| {f} | {wv:+.3f} |")
    lines.append(f"| (bias) | {final_lr['bias']:+.3f} |")
    (OUT / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
