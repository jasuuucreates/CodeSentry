"""The detection pipeline: from submitted source files to scored, explained pairs.

Think of an examiner checking a pile of answer scripts for copying. First every script is
read carefully ONCE and summarised: the handwriting and the names used are ignored, only the
sequence of steps is written down, key phrases are ticked, and an outline of the argument is
sketched. Then every two scripts are laid side by side and the summaries - not the original
pages - are compared: how many ticked phrases they share, and how alike the outlines are. The
two impressions are combined into one judgement, and for the reviewer the matching passages are
marked so the evidence can be checked by eye.

The same steps with their proper names:

1. **prepare** (once per file): tokenize -> normalize (identifiers become ``ID``, comments
   vanish) -> winnow the k-grams into fingerprints -> build the canonical syntax skeleton.
2. **compare** (once per pair): Jaccard similarity of the fingerprint sets (token score), tree
   similarity of the skeletons (structure score), plus the two baselines (plain text and TF-IDF)
   reported alongside for evaluation.
3. **fuse**: weighted mean of token and structure scores, mapped to a High / Moderate / Low
   verdict; shared fingerprints are grouped into matching line regions.

See docs/ARCHITECTURE_CONTRACT.md, section 6, for the exact result shapes.
"""
from __future__ import annotations

import threading
import time
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from .baselines import text_similarity, tfidf_cosine_matrix
from .fusion import fuse, verdict
from .models import (
    EngineConfig,
    EngineError,
    Fingerprint,
    Node,
    SourceFile,
    StructureError,
    Token,
    TokenizeError,
)
from .normalizer import normalize, symbols
from .structure_c import c_skeleton
from .structure_python import python_skeleton
from .tokenizer_c import tokenize_c
from .tokenizer_python import tokenize_python
from .tree_similarity import structural_similarity
from .winnowing import containment, fingerprint, jaccard, kgram_hashes, match_regions

_TOKENIZERS = {"python": tokenize_python, "c": tokenize_c}

# Every score in a result is rounded to this many decimal places.
_DECIMALS = 4

# The C skeleton builder reports syntax errors through a module-level flag, and its tree-sitter
# parser object is shared. The web server handles requests on several threads, so without this
# lock one request could read the flag set by another request's parse (or two threads could use
# the parser at once). Parsing and reading the flag therefore happen as one locked step.
_C_PARSE_LOCK = threading.Lock()

# Size limits of the teaching view produced by explain(): enough to see the idea on screen
# without sending a whole program's worth of tokens to the browser.
_EXPLAIN_TOKENS = 80
_EXPLAIN_KGRAMS = 12
_EXPLAIN_FINGERPRINTS = 40
_EXPLAIN_SKELETON_DEPTH = 6


@dataclass
class PreparedFile:
    """Everything the pipeline needs to know about one file, computed exactly once.

    In a batch of n files there are n(n-1)/2 pairs; preparing each file once instead of once
    per pair means tokenizing, fingerprinting and parsing cost grows with n, not n squared.
    """

    source: SourceFile
    raw_tokens: list[Token]
    tokens: list[Token]             # normalized
    fingerprints: list[Fingerprint]
    skeleton: Node | None
    line_count: int
    warnings: list[str]


# ---------------------------------------------------------------------------------------------
# Stage 1: prepare one file
# ---------------------------------------------------------------------------------------------

def prepare(file: SourceFile, config: EngineConfig) -> PreparedFile:
    """Tokenize, normalize, fingerprint and parse one file.

    A file that cannot be tokenized cannot be compared at all, so :class:`TokenizeError` is
    raised again with the file name in front of the message (the tokenizer only knows the line
    number). A file that tokenizes but does not parse still has a perfectly good token stream,
    so a parse failure only costs the structural score: the skeleton becomes None and a warning
    is recorded. tree-sitter recovers from C syntax errors by itself, so there the skeleton is
    kept and only a warning is added.

    Raises :class:`EngineError` for an unsupported language.
    """
    tokenizer = _TOKENIZERS.get(file.language)
    if tokenizer is None:
        raise EngineError(f"{file.name}: unsupported language {file.language!r}")
    try:
        raw_tokens = tokenizer(file.text)
    except TokenizeError as exc:
        raise TokenizeError(f"{file.name}: {exc}") from exc

    tokens = normalize(raw_tokens, file.language)
    warnings: list[str] = []
    if tokens:
        skeleton = _build_skeleton(file, warnings)
    else:
        # A file of only comments or blank lines parses to an empty "Program" node. Two such
        # files would get a perfect structure score from nothing, so there is nothing to compare.
        skeleton = None
        warnings.append(f"{file.name}: contains no code (only comments or blank lines), "
                        "so it cannot be compared structurally")

    return PreparedFile(
        source=file,
        raw_tokens=raw_tokens,
        tokens=tokens,
        fingerprints=fingerprint(tokens, config.k, config.w),
        skeleton=skeleton,
        line_count=len(file.text.splitlines()),
        warnings=warnings,
    )


def _build_skeleton(file: SourceFile, warnings: list[str]) -> Node | None:
    """Canonical skeleton of `file`, or None (with a warning appended) if it cannot be parsed."""
    try:
        if file.language == "c":
            with _C_PARSE_LOCK:
                skeleton = c_skeleton(file.text)
                had_errors = c_skeleton.last_had_errors
        else:
            skeleton = python_skeleton(file.text)
            had_errors = False
    except StructureError as exc:
        warnings.append(f"{file.name}: {exc}; structural comparison skipped, "
                        "so its pairs are scored on tokens only")
        return None
    if had_errors:
        warnings.append(f"{file.name}: the C parser found syntax errors; "
                        "its structural skeleton may be incomplete")
    return skeleton


# ---------------------------------------------------------------------------------------------
# Stage 2 and 3: compare two prepared files
# ---------------------------------------------------------------------------------------------

def _effective_k(len_a: int, len_b: int, k: int) -> int:
    """k-gram length for a pair (contract short-file rule).

    A stream shorter than k has no k-gram at all, so two tiny but identical snippets would score
    0. For such pairs k shrinks to the shorter stream's length, but never below 2: a single
    token is not a fragment of code.
    """
    shorter = min(len_a, len_b)
    return k if shorter >= k else max(2, shorter)


def _fingerprints_for(prepared: PreparedFile, k_eff: int, config: EngineConfig) -> list[Fingerprint]:
    """The file's fingerprints for this k: reuse the prepared ones unless k had to shrink."""
    if k_eff == config.k:
        return prepared.fingerprints
    return fingerprint(prepared.tokens, k_eff, config.w)


def _rounded(value: float | None) -> float | None:
    return None if value is None else round(value, _DECIMALS)


def compare_prepared(pa: PreparedFile, pb: PreparedFile, config: EngineConfig,
                     tfidf_score: float | None = None) -> dict:
    """Score one pair of prepared files and return a PairResult dictionary.

    `tfidf_score` lets a batch pass in the cosine it already computed with an IDF over the whole
    batch; when it is omitted, the TF-IDF baseline is computed over just these two files.

    The fused score is computed from the unrounded component scores and then rounded, and the
    verdict is taken from that rounded value, so the verdict always agrees with the number the
    user sees.

    Raises :class:`EngineError` if the files are in different languages.
    """
    language = pa.source.language
    if pb.source.language != language:
        raise EngineError(f"cannot compare {pa.source.name} ({language}) with "
                          f"{pb.source.name} ({pb.source.language}): different languages")

    warnings = pa.warnings + pb.warnings
    len_a, len_b = len(pa.tokens), len(pb.tokens)
    k_eff = _effective_k(len_a, len_b, config.k)
    fa = _fingerprints_for(pa, k_eff, config)
    fb = _fingerprints_for(pb, k_eff, config)
    shared = len({f.hash for f in fa} & {f.hash for f in fb})
    shorter = pa if len_a <= len_b else pb

    if min(len_a, len_b) < 2:
        # Not even one 2-gram exists, so fingerprints cannot decide. The only honest token
        # evidence left is whether the two streams are exactly the same.
        token = 1.0 if len_a and symbols(pa.tokens) == symbols(pb.tokens) else 0.0
        contained = token
        matches: list[dict] = []
        warnings.append(f"{shorter.source.name} has fewer than 2 code tokens; its token score is "
                        "1.0 only if both token streams are identical")
    else:
        token = jaccard(fa, fb)
        contained = containment(fa, fb)
        matches = [region.to_dict() for region in match_regions(fa, fb)]
        if k_eff < config.k:
            warnings.append(f"{shorter.source.name} has only {len(shorter.tokens)} code tokens "
                            f"(fewer than k = {config.k}); k-grams of {k_eff} tokens were used")

    if pa.skeleton is not None and pb.skeleton is not None:
        structural = structural_similarity(pa.skeleton, pb.skeleton, config.ted_node_cap)
        structure = structural["structure"]
        ted = structural["ted"]
        subtree = structural["subtree"]
        a_nodes = structural["a_nodes"]
        b_nodes = structural["b_nodes"]
        method = structural["method"]
    else:
        structure = ted = subtree = a_nodes = b_nodes = None
        method = "unavailable"

    if tfidf_score is None:
        tfidf_score = tfidf_cosine_matrix([pa.source.text, pb.source.text])[0][1]

    fused = round(fuse(token, structure, config), _DECIMALS)
    return {
        "a_id": pa.source.id,
        "b_id": pb.source.id,
        "a_name": pa.source.name,
        "b_name": pb.source.name,
        "language": language,
        "scores": {
            "token": _rounded(token),
            "containment": _rounded(contained),
            "structure": _rounded(structure),
            "ted": _rounded(ted),
            "subtree": _rounded(subtree),
            "fused": fused,
            "text_baseline": _rounded(text_similarity(pa.source.text, pb.source.text)),
            "tfidf_baseline": _rounded(tfidf_score),
        },
        "verdict": verdict(fused, config),
        "matches": matches,
        "stats": {
            "a_tokens": len_a,
            "b_tokens": len_b,
            "a_fingerprints": len(fa),
            "b_fingerprints": len(fb),
            "shared_fingerprints": shared,
            "a_nodes": a_nodes,
            "b_nodes": b_nodes,
            "k_effective": k_eff,
            "structure_method": method,
        },
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------------------------

def analyze_pair(a: SourceFile, b: SourceFile, config: EngineConfig | None = None) -> dict:
    """Prepare and compare two files; returns a PairResult.

    Raises :class:`TokenizeError` if either file cannot be tokenized and :class:`EngineError`
    for an unsupported or mismatched language.
    """
    config = config if config is not None else EngineConfig()
    return compare_prepared(prepare(a, config), prepare(b, config), config)


def analyze_batch(files: list[SourceFile], config: EngineConfig | None = None,
                  progress: Callable[[int, int], None] | None = None) -> dict:
    """Compare every same-language pair in a batch of submissions; returns a BatchResult.

    * Every file is prepared exactly once. A file that fails (it cannot be tokenized, or its
      language is unsupported) is still listed with a warning, and every pair involving it is
      skipped (``null`` in the matrix) - one broken upload must not sink the whole class.
    * The TF-IDF baseline gets one IDF per language, computed over that language's files that
      were prepared successfully: a skipped file takes part in no comparison, so it should not
      change the weights of the comparisons that do take place.
    * Files of different languages are never compared (``null`` in the matrix).
    * `progress`, if given, is called as ``progress(0, total)`` before the first comparison and
      ``progress(done, total)`` after each one, where ``total`` is the number of pairs.

    Pairs are sorted by fused score, highest first; pairs with equal scores keep file order.
    """
    config = config if config is not None else EngineConfig()
    started = time.perf_counter()

    prepared: list[PreparedFile | None] = []
    listing: list[dict] = []
    for file in files:
        try:
            item = prepare(file, config)
        except EngineError as exc:
            item = None
            lines, token_count = len(file.text.splitlines()), 0
            file_warnings = [f"{exc}; this file was skipped and is not compared with any other file"]
        else:
            lines, token_count, file_warnings = item.line_count, len(item.tokens), list(item.warnings)
        prepared.append(item)
        listing.append({
            "id": file.id,
            "name": file.name,
            "language": file.language,
            "lines": lines,
            "tokens": token_count,
            "warnings": file_warnings,
        })

    # Group the successfully prepared files by language (indices keep the batch order).
    by_language: dict[str, list[int]] = {}
    for index, item in enumerate(prepared):
        if item is not None:
            by_language.setdefault(item.source.language, []).append(index)

    tfidf: dict[tuple[int, int], float] = {}
    jobs: list[tuple[int, int]] = []
    for indices in by_language.values():
        cosines = tfidf_cosine_matrix([prepared[i].source.text for i in indices])
        for row, i in enumerate(indices):
            for column in range(row + 1, len(indices)):
                j = indices[column]
                tfidf[(i, j)] = cosines[row][column]
                jobs.append((i, j))
    jobs.sort()

    count = len(files)
    matrix: list[list[float | None]] = [[None] * count for _ in range(count)]
    for index in range(count):
        matrix[index][index] = 1.0

    total = len(jobs)
    if progress is not None:
        progress(0, total)
    pairs: list[dict] = []
    for done, (i, j) in enumerate(jobs, 1):
        result = compare_prepared(prepared[i], prepared[j], config, tfidf[(i, j)])
        pairs.append(result)
        matrix[i][j] = matrix[j][i] = result["scores"]["fused"]
        if progress is not None:
            progress(done, total)
    # Python's sort is stable, also with reverse=True, so equal scores keep their file order.
    pairs.sort(key=lambda pair: pair["scores"]["fused"], reverse=True)

    scores = [pair["scores"]["fused"] for pair in pairs]
    verdicts = Counter(pair["verdict"] for pair in pairs)
    summary = {
        "files": count,
        "pairs_compared": len(pairs),
        "high": verdicts["High"],
        "moderate": verdicts["Moderate"],
        "low": verdicts["Low"],
        "max_score": max(scores) if scores else 0.0,
        "mean_score": round(sum(scores) / len(scores), _DECIMALS) if scores else 0.0,
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
    }
    return {
        "files": listing,
        "pairs": pairs,
        "matrix": matrix,
        "summary": summary,
        "config": config.to_dict(),
    }


def explain(code_a: str, code_b: str, language: str, config: EngineConfig | None = None) -> dict:
    """Step-by-step view of how two snippets are compared, for the "How it works" page.

    For each snippet it shows the intermediate products of every stage - raw tokens, the
    normalized symbol stream, the first k-grams with their hashes, the fingerprints winnowing
    kept, and the skeleton - followed by the ordinary PairResult. The k-grams and fingerprints
    use the same effective k as the scores, so what is shown is exactly what was compared.
    Long lists are cut to the first few entries (see the ``_EXPLAIN_*`` limits); ``counts``
    always gives the full sizes.

    Raises :class:`TokenizeError` (message starts with "Snippet A" or "Snippet B") if a snippet
    cannot be tokenized, and :class:`EngineError` for an unsupported language.
    """
    config = config if config is not None else EngineConfig()
    if language not in _TOKENIZERS:
        raise EngineError(f"unsupported language {language!r}; expected 'python' or 'c'")
    pa = prepare(SourceFile(id=1, name="Snippet A", language=language, text=code_a), config)
    pb = prepare(SourceFile(id=2, name="Snippet B", language=language, text=code_b), config)
    result = compare_prepared(pa, pb, config)
    k_eff = result["stats"]["k_effective"]
    return {
        "language": language,
        "a": _explain_side(pa, k_eff, config),
        "b": _explain_side(pb, k_eff, config),
        "result": result,
    }


def _hex(value: int) -> str:
    """A 64-bit hash as the 16-hex-digit string the frontend displays."""
    return f"{value:016x}"


def _explain_side(prepared: PreparedFile, k_eff: int, config: EngineConfig) -> dict:
    """The intermediate products of one snippet, trimmed for display."""
    stream = symbols(prepared.tokens)
    # Hash only the k-grams that are shown: the first _EXPLAIN_KGRAMS k-grams need this many symbols.
    shown_hashes = kgram_hashes(stream[:_EXPLAIN_KGRAMS + k_eff - 1], k_eff)
    fingerprints = _fingerprints_for(prepared, k_eff, config)
    skeleton = prepared.skeleton
    return {
        "raw_tokens": [
            {"kind": token.kind, "value": token.value, "line": token.line}
            for token in prepared.raw_tokens[:_EXPLAIN_TOKENS]
        ],
        "normalized": stream[:_EXPLAIN_TOKENS],
        "kgrams": [
            {"index": index, "text": " ".join(stream[index:index + k_eff]), "hash": _hex(value)}
            for index, value in enumerate(shown_hashes)
        ],
        "fingerprints": [
            {"hash": _hex(f.hash), "position": f.start, "line_start": f.line_start, "line_end": f.line_end}
            for f in fingerprints[:_EXPLAIN_FINGERPRINTS]
        ],
        "skeleton": skeleton.to_dict(max_depth=_EXPLAIN_SKELETON_DEPTH) if skeleton is not None else None,
        "counts": {
            "raw_tokens": len(prepared.raw_tokens),
            "normalized": len(stream),
            "kgrams": max(0, len(stream) - k_eff + 1),
            "fingerprints": len(fingerprints),
            "nodes": skeleton.size() if skeleton is not None else None,
        },
    }
