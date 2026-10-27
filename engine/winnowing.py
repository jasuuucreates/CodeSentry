"""Winnowing: turning a normalized token stream into a small set of position-aware fingerprints.

Reference: S. Schleimer, D. S. Wilkerson and A. Aiken, "Winnowing: Local Algorithms for
Document Fingerprinting", ACM SIGMOD 2003. See docs/ARCHITECTURE_CONTRACT.md, section 4.

The idea in one picture
-----------------------
Two examiners each read a different answer script through a cardboard frame that shows
exactly ``w`` short, overlapping phrases at a time. They slide the frame forward one phrase at
a time, and at every stop they tick the "smallest" phrase visible, using a ranking they agreed
on in advance. The rule looks only at what is inside the frame. So if both scripts contain the
same stretch of text long enough to fill the frame completely, at that stop both examiners see
an identical view and, following the same rule, tick the same phrase. Comparing only the ticked
phrases is therefore enough to catch every shared stretch of that length, while keeping far
fewer phrases than the whole script.

The same picture with its proper names:

* a phrase is a **k-gram** - ``k`` consecutive normalized tokens (:func:`kgram_hashes`);
* the agreed ranking is a **hash** of the k-gram, compared as a number;
* the frame is a **window** of ``w`` consecutive k-gram hashes (:func:`winnow`);
* the ticked phrases are the file's **fingerprints** (:func:`fingerprint`).

Two thresholds follow directly (paper, section 3):

* **noise threshold k** - a shared run shorter than ``k`` tokens contains no complete k-gram,
  so it can never match. This filters out fragments such as ``ID = NUM ;`` that every program
  contains.
* **guarantee threshold t = w + k - 1** - any shared run of at least ``t`` tokens is always
  detected (the reasoning is in :func:`winnow`). With the defaults k = 5, w = 4 that is 8 tokens.
"""
from __future__ import annotations

import hashlib
from collections import deque

from .models import EngineError, Fingerprint, MatchRegion, Token

# Separator placed between symbols before hashing (ASCII "unit separator"). It never occurs in
# a normalized symbol, so the k-grams ("a", "bc") and ("ab", "c") can never hash the same text.
_SEPARATOR = "\x1f"

# At most this many occurrences of one hash are paired per file in match_regions (8 x 8 = 64
# pairs). Common idioms such as "for ID in range (" can occur dozens of times in both files;
# pairing every occurrence with every other would grow quadratically and only add noise.
_OCCURRENCE_CAP = 8


def kgram_hashes(symbols: list[str], k: int) -> list[int]:
    """Hash every k-gram of a symbol stream; element ``i`` is the hash of ``symbols[i:i+k]``.

    What a k-gram is: ``k`` consecutive symbols read as one unit. The stream
    ``ID = ID + NUM`` with k = 3 has the k-grams ``ID = ID``, ``= ID +`` and ``ID + NUM``. A copied
    stretch of code shares its k-grams with the original even when it is surrounded by different
    code, and k decides how long a fragment must be before it counts as evidence.

    Why hash: a k-gram is a list of strings, but winnowing needs to compare and pick a minimum
    quickly. Hashing maps each k-gram to one 64-bit number that acts as a fixed, pseudo-random
    ranking, so the selected minima are spread evenly through the file instead of clustering on
    k-grams that happen to sort first alphabetically. BLAKE2b is used instead of Python's built-in
    ``hash()`` because the built-in string hash is randomised per process: fingerprints must be
    identical across runs. With 64 bits, an accidental collision among a few thousand k-grams is
    astronomically unlikely.

    The contract defines the hash as BLAKE2b-8 of ``"\\x1f".join(symbols[i:i+k])`` encoded as
    UTF-8. Each symbol is encoded once and the bytes are joined, which produces exactly the same
    bytes (UTF-8 encodes a joined string as the join of its encoded parts, and the separator is
    the single byte 0x1f) without re-encoding every symbol k times.

    Returns ``max(0, len(symbols) - k + 1)`` hashes. Raises :class:`EngineError` if ``k < 1``.
    """
    if k < 1:
        raise EngineError(f"k-gram length k must be at least 1 (got {k})")
    encoded = [symbol.encode("utf-8") for symbol in symbols]
    join = _SEPARATOR.encode("utf-8").join
    blake2b = hashlib.blake2b
    from_bytes = int.from_bytes
    return [
        from_bytes(blake2b(join(encoded[i:i + k]), digest_size=8).digest(), "big")
        for i in range(len(encoded) - k + 1)
    ]


def winnow(hashes: list[int], w: int) -> list[tuple[int, int]]:
    """Select fingerprints from k-gram hashes; returns ``(hash, position)`` pairs in position order.

    Rule (contract section 4): slide a window over ``w`` consecutive hashes; in each window select
    the minimum hash, choosing the RIGHTMOST occurrence when the minimum appears more than once;
    record ``(hash, position)`` only when the selected position differs from the one recorded
    last. If ``0 < len(hashes) < w`` there is no complete window, so the rightmost global minimum
    is selected once. Empty input gives ``[]``.

    Why keeping only each window's minimum still catches every shared run of t = w + k - 1
    tokens: such a run contains ``t - k + 1 = w`` complete k-grams, i.e. one full window of ``w``
    hashes that is identical in both files. A hash is selected from every window, and which one
    is decided only by the ``w`` hashes inside that window (the minimum, rightmost on ties) -
    nothing outside the window matters. Both files therefore select the same k-gram hash from that
    window, so the hash appears in both fingerprint lists. Recording only on change never loses
    it: a selection is skipped only when that very position was already recorded for an earlier
    window.

    Why the rightmost tie-break matters: the window moves right, so the leftmost of two equal
    minima is the first to fall out of it, forcing a fresh selection one step later; the rightmost
    one stays inside for the most upcoming windows. For hashes ``[3, 9, 3, 9, 9]`` with w = 3,
    choosing rightmost keeps position 2 for all three windows (one fingerprint), whereas leftmost
    would pick 0 and then 2 (two fingerprints). A fixed rule also makes the selected positions,
    and so the highlighted match regions, reproducible.

    Why record-on-change matters: neighbouring windows share ``w - 1`` hashes, so they usually
    select the same k-gram. Writing it down once instead of once per window keeps about
    2 / (w + 1) of all k-grams (the paper's density for random hashes) and avoids duplicate
    entries that would inflate fingerprint counts and match pairs. Selected positions only ever
    move rightwards, so "differs from the last recorded position" means "not recorded before".

    The paper's *robust* variant adds one refinement: when a new hash equal to the current
    minimum enters the window, it keeps the earlier selection instead of moving to the rightmost.
    That only thins out fingerprints inside long runs of equal hashes. Every window still yields
    the same minimum value, so the SET of selected hashes, and therefore :func:`jaccard` and
    :func:`containment`, are identical under both rules.

    The window minimum is maintained with a monotonic double-ended queue: every position is
    pushed and popped at most once, so the whole pass costs O(n) instead of O(n * w).

    Raises :class:`EngineError` if ``w < 1``.
    """
    if w < 1:
        raise EngineError(f"winnowing window size w must be at least 1 (got {w})")
    n = len(hashes)
    if n == 0:
        return []
    if n < w:
        smallest = min(hashes)
        rightmost = n - 1 - hashes[::-1].index(smallest)
        return [(smallest, rightmost)]

    # Invariant: `window` holds positions left to right whose hashes strictly increase, so its
    # front is the rightmost minimum of the current window. A newly arrived hash that is smaller
    # than or equal to an older one sits further right, so the older one can never again be the
    # rightmost minimum of any window containing both - it is discarded for good.
    window: deque[int] = deque()
    selected: list[tuple[int, int]] = []
    last_recorded = -1
    for position, value in enumerate(hashes):
        while window and hashes[window[-1]] >= value:
            window.pop()
        window.append(position)
        if window[0] <= position - w:
            window.popleft()
        if position >= w - 1:
            chosen = window[0]
            if chosen != last_recorded:
                selected.append((hashes[chosen], chosen))
                last_recorded = chosen
    return selected


def fingerprint(tokens: list[Token], k: int, w: int) -> list[Fingerprint]:
    """Fingerprint a NORMALIZED token stream.

    The canonical symbols (``token.kind``, e.g. ``'ID'``, ``'for'``, ``'+='``) are hashed as
    k-grams and winnowed. Because a renamed variable is still ``'ID'`` and comments never reach
    the normalized stream, renaming and reformatting cannot change the fingerprints.

    The k-gram at position ``p`` covers tokens ``p .. p+k-1``; each fingerprint keeps those token
    indices and the source lines they span (``tokens[p].line`` to ``tokens[p+k-1].end_line``) so a
    match can be highlighted in the original file. A stream shorter than ``k`` has no k-gram and
    yields ``[]``.
    """
    hashes = kgram_hashes([token.kind for token in tokens], k)
    return [
        Fingerprint(
            hash=value,
            start=position,
            end=position + k - 1,
            line_start=tokens[position].line,
            line_end=tokens[position + k - 1].end_line,
        )
        for value, position in winnow(hashes, w)
    ]


def jaccard(fa: list[Fingerprint], fb: list[Fingerprint]) -> float:
    """Share of distinct fingerprint hashes the two files have in common: ``|A n B| / |A u B|``.

    Sets are used because what matters is which fragments occur in both files, not how often a
    common idiom repeats. 1.0 means identical fingerprint sets; 0.0 is also returned when both
    files have no fingerprints at all, since there is then no evidence of copying.
    """
    hashes_a = {f.hash for f in fa}
    hashes_b = {f.hash for f in fb}
    union = len(hashes_a | hashes_b)
    if union == 0:
        return 0.0
    return len(hashes_a & hashes_b) / union


def containment(fa: list[Fingerprint], fb: list[Fingerprint]) -> float:
    """Share of the SMALLER file's distinct hashes found in the other: ``|A n B| / min(|A|, |B|)``.

    Jaccard punishes size differences: a short program copied whole into a long one has a low
    Jaccard score but a containment of 1.0, which is the signal a reviewer needs. 0.0 if either
    file has no fingerprints.
    """
    hashes_a = {f.hash for f in fa}
    hashes_b = {f.hash for f in fb}
    smaller = min(len(hashes_a), len(hashes_b))
    if smaller == 0:
        return 0.0
    return len(hashes_a & hashes_b) / smaller


def match_regions(fa: list[Fingerprint], fb: list[Fingerprint]) -> list[MatchRegion]:
    """Group shared fingerprints into blocks of lines that match between file A and file B.

    1. **Pair.** For every hash present in both files, pair each of its occurrences in A with each
       occurrence in B, using at most the first 8 occurrences per file (at most 64 pairs per hash).
    2. **Merge.** Two pairs belong to the same region when their A line ranges overlap or are
       adjacent (gap of at most 1 line) AND their B line ranges do too. Regions are the connected
       groups under this rule, so a copied block of code is chained together from the overlapping
       k-grams inside it.
    3. **Summarise.** A region spans the lowest to highest line of its k-grams in each file;
       ``tokens`` counts the distinct token positions in A covered by its k-grams.
    4. **Clean up.** A region lying entirely inside another adds nothing and is dropped (of two
       identical boxes, the one covering more tokens is kept). The rest are sorted by
       ``(a_start, b_start)``.

    How the merge stays fast: ranges ``[s1, e1]`` and ``[s2, e2]`` are within one line of each
    other exactly when ``[s1, e1 + 1]`` and ``[s2, e2 + 1]`` share at least one line. Every pair is
    therefore listed once under each line of its widened A range; two pairs that should merge are
    always listed together under some A line. Within one A line the widened B ranges are swept in
    order of their start while tracking the furthest end reached so far, which finds every
    overlapping chain in a single pass. Pairs are joined with a union-find structure. A k-gram
    covers only a few lines, so the work grows roughly linearly with the number of pairs.
    """
    occurrences_a = _first_occurrences(fa)
    occurrences_b = _first_occurrences(fb)
    pairs: list[tuple[Fingerprint, Fingerprint]] = []
    for value, in_a in occurrences_a.items():
        in_b = occurrences_b.get(value)
        if in_b:
            pairs.extend((x, y) for x in in_a for y in in_b)
    if not pairs:
        return []

    parent = list(range(len(pairs)))

    def find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]  # path halving keeps later look-ups short
            i = parent[i]
        return i

    # One entry per (widened A line, pair): (a_line, b_from, b_to_widened, pair index).
    entries = [
        (a_line, y.line_start, y.line_end + 1, index)
        for index, (x, y) in enumerate(pairs)
        for a_line in range(x.line_start, x.line_end + 2)
    ]
    entries.sort()

    current_line = None
    reach = holder = 0
    for a_line, b_from, b_to, index in entries:
        if a_line != current_line or b_from > reach:
            # A new A line, or a gap in B: nothing seen so far on this line can touch this pair.
            current_line, reach, holder = a_line, b_to, index
            continue
        # `holder` starts at or before b_from and ends at `reach` >= b_from: the B ranges overlap.
        root_a, root_b = find(holder), find(index)
        if root_a != root_b:
            parent[max(root_a, root_b)] = min(root_a, root_b)
        if b_to > reach:
            reach, holder = b_to, index

    groups: dict[int, list[int]] = {}
    for index in range(len(pairs)):
        groups.setdefault(find(index), []).append(index)

    regions = []
    for members in groups.values():
        a_side = [pairs[i][0] for i in members]
        b_side = [pairs[i][1] for i in members]
        regions.append(MatchRegion(
            a_start=min(f.line_start for f in a_side),
            a_end=max(f.line_end for f in a_side),
            b_start=min(f.line_start for f in b_side),
            b_end=max(f.line_end for f in b_side),
            tokens=_covered_positions({(f.start, f.end) for f in a_side}),
        ))

    kept = _drop_contained(regions)
    kept.sort(key=lambda r: (r.a_start, r.b_start, r.a_end, r.b_end))
    return kept


def _first_occurrences(fingerprints: list[Fingerprint]) -> dict[int, list[Fingerprint]]:
    """Map each hash to its first `_OCCURRENCE_CAP` fingerprints, in input order."""
    occurrences: dict[int, list[Fingerprint]] = {}
    for f in fingerprints:
        bucket = occurrences.setdefault(f.hash, [])
        if len(bucket) < _OCCURRENCE_CAP:
            bucket.append(f)
    return occurrences


def _covered_positions(spans: set[tuple[int, int]]) -> int:
    """Number of distinct integers covered by inclusive ``(start, end)`` spans.

    Overlapping k-grams share tokens, so spans are merged in start order rather than summed.
    """
    total = 0
    reach = -1  # highest position counted so far
    for start, end in sorted(spans):
        if end > reach:
            total += end - max(start, reach + 1) + 1
            reach = end
    return total


def _drop_contained(regions: list[MatchRegion]) -> list[MatchRegion]:
    """Remove every region whose line box lies inside another region's box.

    Sorting by (a_start, -a_end, b_start, -b_end, -tokens) places any container before the regions
    it contains, so each region only needs checking against regions already kept. A kept region
    whose A range ends before the current region starts cannot contain it or anything later in
    the order, so it is retired from the list of candidates.
    """
    ordered = sorted(regions, key=lambda r: (r.a_start, -r.a_end, r.b_start, -r.b_end, -r.tokens))
    kept: list[MatchRegion] = []
    candidates: list[MatchRegion] = []
    for region in ordered:
        candidates = [c for c in candidates if c.a_end >= region.a_start]
        if any(c.a_end >= region.a_end and c.b_start <= region.b_start and c.b_end >= region.b_end
               for c in candidates):
            continue
        kept.append(region)
        candidates.append(region)
    return kept
