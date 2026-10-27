"""Baselines (plain text, TF-IDF) and fusion / verdict (contract section 6)."""
import math

import pytest

from engine.baselines import cosine, text_similarity, tfidf_cosine_matrix, tfidf_vectors
from engine.fusion import fuse, verdict
from engine.models import EngineConfig, EngineError


def test_text_similarity():
    a = "x = 1\ny = 2\nprint(x + y)\n"
    assert text_similarity(a, a) == 1.0
    assert text_similarity(a, "x = 1\ny = 3\nprint(x + y)\n") == pytest.approx(2 / 3)
    assert text_similarity(a, "completely\ndifferent\n") == 0.0


def test_tfidf_smoothed_idf_and_l2_norm():
    vectors = tfidf_vectors(["alpha beta", "alpha gamma"])
    idf_alpha = math.log(3 / 3) + 1          # in both documents
    idf_beta = math.log(3 / 2) + 1           # in one document
    norm = math.sqrt(idf_alpha ** 2 + idf_beta ** 2)
    assert vectors[0]["alpha"] == pytest.approx(idf_alpha / norm)
    assert vectors[0]["beta"] == pytest.approx(idf_beta / norm)
    for vector in vectors:
        assert sum(w * w for w in vector.values()) == pytest.approx(1.0)


def test_tfidf_lowercases_and_counts_repeats():
    vectors = tfidf_vectors(["Total total x", "y"])
    assert set(vectors[0]) == {"total", "x"}
    assert vectors[0]["total"] > vectors[0]["x"]


def test_cosine_and_matrix():
    assert cosine({"a": 1.0}, {"a": 1.0}) == pytest.approx(1.0)
    assert cosine({"a": 1.0}, {"b": 1.0}) == 0.0
    matrix = tfidf_cosine_matrix(["a b c", "a b d", "x y z"])
    assert [matrix[i][i] for i in range(3)] == pytest.approx([1.0, 1.0, 1.0])
    assert matrix[0][1] == pytest.approx(matrix[1][0])
    assert matrix[0][1] > matrix[0][2]
    assert matrix[0][2] == 0.0


def test_fuse_weighted_mean_and_missing_structure():
    config = EngineConfig()
    assert fuse(0.8, 0.4, config) == pytest.approx(0.6)
    assert fuse(0.8, None, config) == 0.8
    skewed = EngineConfig(w_token=3.0, w_structure=1.0)
    assert fuse(1.0, 0.0, skewed) == pytest.approx(0.75)
    assert fuse(0.8, 0.4, EngineConfig(w_token=0.6, w_structure=0.6)) == pytest.approx(0.6)
    with pytest.raises(EngineError):
        fuse(0.5, 0.5, EngineConfig(w_token=0.0, w_structure=0.0))


def test_verdict_thresholds_are_inclusive():
    config = EngineConfig()
    assert verdict(0.75, config) == "High"
    assert verdict(0.7499, config) == "Moderate"
    assert verdict(0.5, config) == "Moderate"
    assert verdict(0.4999, config) == "Low"


def test_config_round_trip_and_validation():
    config = EngineConfig.from_dict({"k": 7, "unknown_key": 1})
    assert config.k == 7
    assert EngineConfig.from_dict(config.to_dict()) == config
    assert EngineConfig.from_dict(None) == EngineConfig()
    with pytest.raises(EngineError):
        EngineConfig.from_dict({"k": 0})
