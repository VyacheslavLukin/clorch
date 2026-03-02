"""Cost calculation per model based on Anthropic pricing (2026)."""
from __future__ import annotations

import re

# Pricing per 1M tokens: (input, cache_write_5m, cache_read, output)
# Source: https://docs.anthropic.com/en/docs/about-claude/pricing
MODEL_PRICING: dict[str, tuple[float, float, float, float]] = {
    # Opus 4.5 / 4.6
    "opus-4-5": (5.0, 6.25, 0.50, 25.0),
    "opus-4-6": (5.0, 6.25, 0.50, 25.0),
    # Opus 4 / 4.1 (legacy)
    "opus-4-1": (15.0, 18.75, 1.50, 75.0),
    "opus-4-0": (15.0, 18.75, 1.50, 75.0),
    # Sonnet (same across 3.7 / 4 / 4.5 / 4.6)
    "sonnet": (3.0, 3.75, 0.30, 15.0),
    # Haiku 4.5+
    "haiku-4-5": (1.0, 1.25, 0.10, 5.0),
    # Haiku 3.5 (legacy)
    "haiku-3-5": (0.80, 1.00, 0.08, 4.0),
}

# Fallback tiers for family-only matches (no version)
_FAMILY_FALLBACK: dict[str, str] = {
    "opus": "opus-4-6",
    "haiku": "haiku-4-5",
}

# Default fallback for completely unknown models
_DEFAULT_TIER = "sonnet"

# Pattern: claude-{family}-{major}-{minor}  e.g. claude-opus-4-6
_MODEL_RE = re.compile(r"(opus|sonnet|haiku)[- ]*(\d+)[- ]*(\d+)?", re.IGNORECASE)


def _resolve_pricing(model: str) -> tuple[float, float, float, float]:
    """Resolve a model name string to its pricing tuple.

    Tries versioned match first (e.g. 'opus-4-6'), then family fallback.
    """
    m = _MODEL_RE.search(model)
    if m:
        family = m.group(1).lower()
        major = m.group(2)
        minor = m.group(3) or "0"
        versioned_key = f"{family}-{major}-{minor}"
        if versioned_key in MODEL_PRICING:
            return MODEL_PRICING[versioned_key]
        # Sonnet — all versions same price
        if family in MODEL_PRICING:
            return MODEL_PRICING[family]
        # Family fallback (opus -> opus-4-6, haiku -> haiku-4-5)
        fallback = _FAMILY_FALLBACK.get(family)
        if fallback:
            return MODEL_PRICING[fallback]
    # Substring fallback for weird model strings
    model_lower = model.lower()
    for key in MODEL_PRICING:
        if key in model_lower:
            return MODEL_PRICING[key]
    return MODEL_PRICING[_DEFAULT_TIER]


def calculate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_write_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> float:
    """Calculate cost in dollars for given token counts and model."""
    all_zero = (input_tokens == 0 and output_tokens == 0
                and cache_write_tokens == 0 and cache_read_tokens == 0)
    if all_zero:
        return 0.0

    price_input, price_cache_write, price_cache_read, price_output = (
        _resolve_pricing(model)
    )
    cost = (
        input_tokens * price_input
        + cache_write_tokens * price_cache_write
        + cache_read_tokens * price_cache_read
        + output_tokens * price_output
    ) / 1_000_000
    return cost
