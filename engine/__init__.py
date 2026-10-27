"""CodeSentry detection engine: the public interface used by the backend and the evaluation.

Callers only need this package namespace::

    from engine import EngineConfig, SourceFile, analyze_batch

The individual stages (tokenizers, normalizer, winnowing, structure, baselines, fusion) live in
their own modules and can be imported directly when a test or the explanation view needs them.
See docs/ARCHITECTURE_CONTRACT.md, section 6.
"""
from .lang import detect_language
from .models import EngineConfig, EngineError, SourceFile, StructureError, TokenizeError
from .pipeline import analyze_batch, analyze_pair, explain

__version__ = "1.0.0"

SUPPORTED_LANGUAGES = ("python", "c")

__all__ = [
    "EngineConfig",
    "SourceFile",
    "EngineError",
    "TokenizeError",
    "StructureError",
    "detect_language",
    "analyze_pair",
    "analyze_batch",
    "explain",
    "SUPPORTED_LANGUAGES",
    "__version__",
]
