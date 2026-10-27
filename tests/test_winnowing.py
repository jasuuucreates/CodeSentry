"""Winnowing fingerprints (contract section 4, Schleimer et al. 2003)."""
import hashlib

from engine.models import Token
from engine.normalizer import normalize
from engine.tokenizer_python import tokenize_python
from engine.winnowing import containment, fingerprint, jaccard, kgram_hashes, match_regions, winnow


def test_kgram_count_and_hash_definition():
    symbols = ["ID", "=", "ID", "+", "NUM"]
    hashes = kgram_hashes(symbols, 3)
    assert len(hashes) == 3
    expected = int.from_bytes(hashlib.blake2b("ID\x1f=\x1fID".encode("utf-8"), digest_size=8).digest(), "big")
    assert hashes[0] == expected
    assert kgram_hashes(symbols, 6) == []


def test_winnow_selects_rightmost_minimum_on_ties():
    # windows (w=2): [5,1] -> pos 1; [1,1] -> tie, rightmost pos 2; [1,3] -> pos 2 again (not re-recorded)
    assert winnow([5, 1, 1, 3], 2) == [(1, 1), (1, 2)]


def test_winnow_records_only_when_selection_moves():
    assert winnow([3, 2, 4, 5, 1], 3) == [(2, 1), (1, 4)]


def test_winnow_short_and_empty_inputs():
    assert winnow([4, 2, 2], 5) == [(2, 2)]       # fewer hashes than w: rightmost global minimum once
    assert winnow([], 4) == []


def _tokens(text):
    return normalize(tokenize_python(text), "python")


def test_fingerprint_line_numbers():
    tokens = _tokens("a = 1\nb = a + 2\nc = b * a\n")
    prints = fingerprint(tokens, 3, 2)
    assert prints
    for fp in prints:
        assert fp.end == fp.start + 2
        assert fp.line_start == tokens[fp.start].line
        assert fp.line_end == tokens[fp.end].end_line


def test_jaccard_and_containment():
    text = "x = 1\nfor i in range(10):\n    x = x * i + 3\nprint(x)\n"
    other = "def f(a, b):\n    return [a] * b\n"
    fa = fingerprint(_tokens(text), 3, 2)
    fb = fingerprint(_tokens(other), 3, 2)
    assert jaccard(fa, fa) == 1.0
    assert jaccard(fa, fb) < 0.3
    assert jaccard([], []) == 0.0
    assert containment(fa, fa[:3]) == 1.0          # every fingerprint of the smaller set is shared
    assert containment(fa, []) == 0.0


def test_match_regions_cover_identical_code():
    text = "total = 0\nfor i in range(10):\n    total += i\nprint(total)\n"
    fa = fingerprint(_tokens(text), 3, 2)
    regions = match_regions(fa, fa)
    assert regions
    assert regions[0].a_start == 1 and regions[0].b_start == 1
    assert max(r.a_end for r in regions) == 4
    assert all(r.tokens > 0 for r in regions)


def test_match_regions_empty_when_nothing_shared():
    a = fingerprint(_tokens("x = 1\ny = 2\n"), 3, 2)
    b = fingerprint(_tokens("def f():\n    return [1, 2]\n"), 3, 2)
    assert match_regions(a, b) == []
