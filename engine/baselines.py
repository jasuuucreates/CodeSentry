"""Baseline similarity measures that CodeSentry is compared against.

A detector is only convincing if it beats the simple methods a teacher might already use, so
two conventional baselines are implemented here with every formula written out explicitly:

* **Plain text matching** (:func:`text_similarity`): how many source lines the two files share,
  in order, exactly as written. Renaming one variable changes every line that mentions it, so
  this measure is easy to fool.
* **TF-IDF cosine** (:func:`tfidf_vectors`, :func:`cosine`): the bag-of-words method used in
  information retrieval. Each file becomes a vector of word weights; files that use the same
  distinctive words point in similar directions. Word order is ignored and raw identifier names
  are kept, which is exactly why renaming and restructuring hurt it.

See docs/ARCHITECTURE_CONTRACT.md, section 6. Pure standard library: no numpy or scikit-learn,
so the arithmetic can be checked by hand.
"""
from __future__ import annotations

import difflib
import math
import re
from collections import Counter

# A "word" is an identifier or keyword, a run of digits, or any single punctuation character.
WORD_RE = r"[A-Za-z_][A-Za-z0-9_]*|\d+|[^\sA-Za-z0-9_]"
_WORD_PATTERN = re.compile(WORD_RE)


def text_similarity(a_text: str, b_text: str) -> float:
    """Plain-text baseline: ``difflib.SequenceMatcher`` ratio over the lines of both files.

    Lines are compared exactly as written (``str.splitlines()`` and nothing else), because the
    point of this baseline is to show what happens WITHOUT normalization. The ratio is
    ``2 * matched_lines / (lines_a + lines_b)``, where matched lines are found as the longest
    common in-order blocks. ``autojunk=False`` stops difflib from silently ignoring lines that
    occur very often (such as a lone closing brace), which would make the result depend on a
    hidden heuristic.
    """
    matcher = difflib.SequenceMatcher(None, a_text.splitlines(), b_text.splitlines(), autojunk=False)
    return matcher.ratio()


def _terms(text: str) -> Counter[str]:
    """Raw term counts of one document: every WORD_RE match, lower-cased."""
    return Counter(match.lower() for match in _WORD_PATTERN.findall(text))


def tfidf_vectors(texts: list[str]) -> list[dict[str, float]]:
    """One L2-normalized TF-IDF vector (term -> weight) per text.

    * ``tf``  = how many times the term occurs in this document (raw count);
    * ``df``  = in how many of the N documents the term occurs at least once;
    * ``idf`` = ``ln((1 + N) / (1 + df)) + 1`` - the smoothed formula scikit-learn uses. A term
      found in every document gets idf 1 (it says little), a rare term gets a larger idf; the
      ``+ 1`` terms avoid division by zero and keep every weight positive;
    * ``weight = tf * idf``, and finally every vector is divided by its Euclidean length, so a
      long file and a short file with the same word proportions get the same vector.

    A text with no terms at all gets an empty vector.
    """
    counts = [_terms(text) for text in texts]
    total_documents = len(counts)
    document_frequency: Counter[str] = Counter()
    for document in counts:
        document_frequency.update(document.keys())
    idf = {
        term: math.log((1 + total_documents) / (1 + frequency)) + 1
        for term, frequency in document_frequency.items()
    }

    vectors: list[dict[str, float]] = []
    for document in counts:
        weights = {term: count * idf[term] for term, count in document.items()}
        length = math.sqrt(sum(weight * weight for weight in weights.values()))
        vectors.append({term: weight / length for term, weight in weights.items()} if length else {})
    return vectors


def cosine(u: dict[str, float], v: dict[str, float]) -> float:
    """Cosine of the angle between two sparse vectors: ``(u . v) / (|u| |v|)``.

    Only terms present in both vectors contribute to the dot product, so the loop runs over the
    smaller vector. Returns 0.0 when either vector is empty (no shared terms means no evidence).
    The result is clamped to [-1, 1] because floating-point rounding can overshoot 1 by a hair
    for identical vectors.
    """
    if len(u) > len(v):
        u, v = v, u
    dot = sum(weight * v.get(term, 0.0) for term, weight in u.items())
    if dot == 0.0:
        return 0.0
    norm_u = math.sqrt(sum(weight * weight for weight in u.values()))
    norm_v = math.sqrt(sum(weight * weight for weight in v.values()))
    return max(-1.0, min(1.0, dot / (norm_u * norm_v)))


def tfidf_cosine_matrix(texts: list[str]) -> list[list[float]]:
    """Symmetric matrix of TF-IDF cosine similarities between every pair of texts.

    The IDF is computed over exactly the texts given, so the same pair of files can score
    differently in a different batch: a word shared by the whole class carries less weight than
    a word only two students used. Each cell is computed once and mirrored.
    """
    vectors = tfidf_vectors(texts)
    size = len(vectors)
    matrix = [[0.0] * size for _ in range(size)]
    for i in range(size):
        for j in range(i, size):
            matrix[i][j] = matrix[j][i] = cosine(vectors[i], vectors[j])
    return matrix
