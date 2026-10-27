# CodeSentry - evaluation summary

Generated 2026-10-27T12:20:23+05:30 by `evaluation/evaluate.py` from `dataset/labels.json`.
Every number below comes from running the script; nothing is entered by hand.
Engine settings: the untrained defaults, `EngineConfig()` (k = 5, w = 4, w_token = 0.5, w_structure = 0.5).

## Dataset

* 290 labelled pairs: 120 copied (positive), 170 independent (negative)
* by language: c 145, python 145
* by category: rename 20, comments_format 20, reorder 20, loop_swap 20, dead_code 20, combined 20, independent_same_problem 60, obfuscated_vs_independent 20, different_problem 90

## Results at the fixed default threshold 0.50

A pair is flagged when its score is >= 0.50.

| Method | Precision | Recall | F1 | Accuracy | ROC AUC | TP | FP | TN | FN | ms / pair |
|---|---|---|---|---|---|---|---|---|---|---|
| Plain text matching (difflib, raw lines) | 1.000 | 0.575 | 0.730 | 0.824 | 0.804 | 69 | 0 | 170 | 51 | 0.24 |
| TF-IDF cosine (raw words) | 0.471 | 0.892 | 0.617 | 0.541 | 0.843 | 107 | 120 | 50 | 13 | 0.28 |
| Token winnowing (Jaccard of fingerprints) | 1.000 | 0.967 | 0.983 | 0.986 | 1.000 | 116 | 0 | 170 | 4 | 2.81 |
| Structure (AST tree similarity) | 0.992 | 1.000 | 0.996 | 0.997 | 1.000 | 120 | 1 | 169 | 0 | 7.09 |
| Hybrid (token + structure) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 120 | 0 | 170 | 0 | 9.41 |

## Best-F1 threshold (tuned on this same dataset - optimistic)

The threshold in 0.00, 0.01, ..., 1.00 that maximises F1 for each method. It is chosen on the
data it is measured on, so these figures are an upper bound, not an unbiased estimate.

| Method | Threshold | Precision | Recall | F1 | Accuracy |
|---|---|---|---|---|---|
| Plain text matching (difflib, raw lines) | 0.34 | 1.000 | 0.683 | 0.812 | 0.869 |
| TF-IDF cosine (raw words) | 0.74 | 0.975 | 0.650 | 0.780 | 0.848 |
| Token winnowing (Jaccard of fingerprints) | 0.24 | 1.000 | 1.000 | 1.000 | 1.000 |
| Structure (AST tree similarity) | 0.51 | 1.000 | 1.000 | 1.000 | 1.000 |
| Hybrid (token + structure) | 0.36 | 1.000 | 1.000 | 1.000 | 1.000 |

## Recall per obfuscation category (threshold 0.50)

| Method | rename | comments_format | reorder | loop_swap | dead_code | combined |
|---|---|---|---|---|---|---|
| text | 0.400 | 0.500 | 0.550 | 1.000 | 1.000 | 0.000 |
| tfidf | 0.850 | 1.000 | 1.000 | 1.000 | 1.000 | 0.500 |
| token | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 0.800 |
| structure | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| hybrid | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## False-positive rate per negative category (threshold 0.50)

| Method | independent_same_problem | obfuscated_vs_independent | different_problem |
|---|---|---|---|
| text | 0.000 | 0.000 | 0.000 |
| tfidf | 0.783 | 0.100 | 0.789 |
| token | 0.000 | 0.000 | 0.000 |
| structure | 0.017 | 0.000 | 0.000 |
| hybrid | 0.000 | 0.000 | 0.000 |

## Trained models, grouped cross-validation (see training/results/summary.md)

Merged from `evaluation/results/training_cv.json`, written by `training/train_model.py`.

| Method | Precision | Recall | F1 | Accuracy | ROC AUC |
|---|---|---|---|---|---|
| Calibrated hybrid (trained, 5-fold grouped CV) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| Logistic regression (trained, 5-fold grouped CV) | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

## Notes

* ROC AUC uses the rank (Mann-Whitney U) formula with ties counted as 0.5.
* ms / pair is the wall time of a full pass over all pairs divided by the number of pairs;
  one-off per-file work (TF-IDF vectors, fingerprints, skeletons) is included in that pass.
* Per-pair scores for every method are in `pair_scores.csv`.
