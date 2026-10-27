"""Optional trained classifier: adds ``scores.ml_probability`` to pair results.

``training/train_model.py`` fits a logistic regression on the labelled dataset and writes
``engine/trained_model.json``::

    {"features": ["token", "containment", "structure", "ted", "subtree", "text", "tfidf", "length_ratio"],
     "means": [...], "stds": [...], "weights": [...], "bias": 0.0, "threshold": 0.5, "meta": {...}}

For a pair, every feature x[j] is standardised with the training mean and standard deviation and

    p = 1 / (1 + exp(-(bias + sum_j weights[j] * (x[j] - means[j]) / stds[j])))

is the model's probability that the pair is plagiarised. The detection verdict itself still comes
from the fused score; the probability is an extra, clearly labelled signal. Without the file the
key is simply omitted.
"""
from __future__ import annotations

import json
import logging
import math
from pathlib import Path

log = logging.getLogger("codesentry")

KNOWN_FEATURES = ("token", "containment", "structure", "ted", "subtree", "text", "tfidf", "length_ratio")


def load_model(path: str | None) -> dict | None:
    """The model stored at ``path``, or None if there is none (or it is invalid: logged)."""
    if not path or not Path(path).is_file():
        return None
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        features = list(data["features"])
        means = [float(v) for v in data["means"]]
        stds = [float(v) for v in data["stds"]]
        weights = [float(v) for v in data["weights"]]
        bias = float(data["bias"])
        unknown = [f for f in features if f not in KNOWN_FEATURES]
        if unknown:
            raise ValueError(f"unknown feature(s) {unknown}")
        if not (len(features) == len(means) == len(stds) == len(weights)) or not features:
            raise ValueError("features, means, stds and weights must have the same non-zero length")
        # A feature that never varied in training has std 0; it then contributes nothing useful,
        # so divide by 1 instead of crashing.
        stds = [s if s > 0 else 1.0 for s in stds]
        return {"features": features, "means": means, "stds": stds, "weights": weights, "bias": bias,
                "threshold": float(data.get("threshold", 0.5)), "meta": data.get("meta")}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        log.warning("Ignoring trained model %s (%s); ml_probability will not be reported.", path, exc)
        return None


def _features(pair: dict) -> dict[str, float]:
    """The model's input features, read from a PairResult."""
    scores, stats = pair.get("scores", {}), pair.get("stats", {})
    token = float(scores.get("token") or 0.0)
    structure = scores.get("structure")
    structure = token if structure is None else float(structure)
    ted, subtree = scores.get("ted"), scores.get("subtree")
    a_tokens, b_tokens = stats.get("a_tokens") or 0, stats.get("b_tokens") or 0
    longest = max(a_tokens, b_tokens)
    return {
        "token": token,
        "containment": float(scores.get("containment") or 0.0),
        "structure": structure,
        "ted": structure if ted is None else float(ted),
        "subtree": structure if subtree is None else float(subtree),
        "text": float(scores.get("text_baseline") or 0.0),
        "tfidf": float(scores.get("tfidf_baseline") or 0.0),
        "length_ratio": (min(a_tokens, b_tokens) / longest) if longest else 0.0,
    }


def probability(model: dict, pair: dict) -> float:
    """Logistic-regression probability (rounded to 4 decimals) that ``pair`` is plagiarised."""
    x = _features(pair)
    z = model["bias"]
    for name, mean, std, weight in zip(model["features"], model["means"], model["stds"], model["weights"]):
        z += weight * (x[name] - mean) / std
    # Numerically stable sigmoid (no overflow for large |z|).
    if z >= 0:
        p = 1.0 / (1.0 + math.exp(-z))
    else:
        e = math.exp(z)
        p = e / (1.0 + e)
    return round(p, 4)


def annotate(model: dict | None, pair: dict) -> dict:
    """Adds ``scores.ml_probability`` to ``pair`` in place (no-op without a model); returns it."""
    if model is not None:
        pair.setdefault("scores", {})["ml_probability"] = probability(model, pair)
    return pair
