"""Score fusion: combine the token score and the structural score into one verdict.

The two stages catch different kinds of disguise. Winnowing (token score) is precise about
copied stretches of code but loses them when statements are reordered or loops rewritten; the
syntax-tree comparison (structure score) survives those edits but on its own is less precise,
because unrelated programs for the same assignment often have similar shapes. A weighted mean
lets each stage cover the other's blind spot. See docs/ARCHITECTURE_CONTRACT.md, section 6.
"""
from __future__ import annotations

from .models import EngineConfig, EngineError


def fuse(token: float, structure: float | None, config: EngineConfig) -> float:
    """Weighted mean of the token and structure scores.

    ``fused = (w_token * token + w_structure * structure) / (w_token + w_structure)``

    Dividing by the sum of the weights means the weights need not add up to 1 (0.6 and 0.6 act
    like 0.5 and 0.5), so the result always stays between the two input scores. When the
    structure score is missing - the file could not be parsed - the token score is returned
    unchanged rather than treating the missing score as 0, which would unfairly lower the
    result for a file that merely has a syntax error.

    Raises :class:`EngineError` if both weights are 0, since no mean is then defined.
    """
    if structure is None:
        return token
    total_weight = config.w_token + config.w_structure
    if total_weight <= 0:
        raise EngineError("w_token and w_structure cannot both be 0")
    return (config.w_token * token + config.w_structure * structure) / total_weight


def verdict(score: float, config: EngineConfig) -> str:
    """``"High"`` at or above `high_threshold`, ``"Moderate"`` at or above `moderate_threshold`,
    otherwise ``"Low"``.

    The verdict only ranks pairs for a human reviewer; it is not an accusation. Thresholds are
    inclusive so that a score shown as exactly 0.75 is never labelled below "High".
    """
    if score >= config.high_threshold:
        return "High"
    if score >= config.moderate_threshold:
        return "Moderate"
    return "Low"
