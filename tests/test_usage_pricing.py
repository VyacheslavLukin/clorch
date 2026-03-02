"""Tests for clorch.usage.pricing."""
from __future__ import annotations

from clorch.usage.pricing import MODEL_PRICING, _resolve_pricing, calculate_cost


class TestResolvePricing:
    def test_opus_46(self):
        assert _resolve_pricing("claude-opus-4-6") == MODEL_PRICING["opus-4-6"]

    def test_opus_45(self):
        assert _resolve_pricing("claude-opus-4-5") == MODEL_PRICING["opus-4-5"]

    def test_opus_41_legacy(self):
        assert _resolve_pricing("claude-opus-4-1") == MODEL_PRICING["opus-4-1"]

    def test_sonnet_model(self):
        assert _resolve_pricing("claude-sonnet-4-6") == MODEL_PRICING["sonnet"]

    def test_haiku_45(self):
        assert _resolve_pricing("claude-haiku-4-5-20251001") == MODEL_PRICING["haiku-4-5"]

    def test_haiku_35_legacy(self):
        assert _resolve_pricing("claude-haiku-3-5") == MODEL_PRICING["haiku-3-5"]

    def test_unknown_falls_back_to_sonnet(self):
        assert _resolve_pricing("unknown-model-xyz") == MODEL_PRICING["sonnet"]

    def test_case_insensitive(self):
        assert _resolve_pricing("Claude-Opus-4-6") == MODEL_PRICING["opus-4-6"]


class TestCalculateCost:
    def test_zero_tokens(self):
        assert calculate_cost("claude-opus-4-6") == 0.0

    def test_opus_46_input_only(self):
        # Opus 4.6: 1M input at $5/1M = $5.00
        cost = calculate_cost("claude-opus-4-6", input_tokens=1_000_000)
        assert abs(cost - 5.0) < 0.001

    def test_opus_46_output_only(self):
        # Opus 4.6: 1M output at $25/1M = $25.00
        cost = calculate_cost("claude-opus-4-6", output_tokens=1_000_000)
        assert abs(cost - 25.0) < 0.001

    def test_opus_46_cache_write(self):
        # Opus 4.6: 1M cache write at $6.25/1M
        cost = calculate_cost("claude-opus-4-6", cache_write_tokens=1_000_000)
        assert abs(cost - 6.25) < 0.001

    def test_opus_46_cache_read(self):
        # Opus 4.6: 1M cache read at $0.50/1M
        cost = calculate_cost("claude-opus-4-6", cache_read_tokens=1_000_000)
        assert abs(cost - 0.50) < 0.001

    def test_opus_41_legacy_more_expensive(self):
        # Opus 4.1: 1M input at $15/1M (3x more than 4.6)
        cost = calculate_cost("claude-opus-4-1", input_tokens=1_000_000)
        assert abs(cost - 15.0) < 0.001

    def test_sonnet_mixed(self):
        # 500K input ($3 * 0.5 = $1.5) + 100K output ($15 * 0.1 = $1.5) = $3.00
        cost = calculate_cost(
            "claude-sonnet-4-6",
            input_tokens=500_000,
            output_tokens=100_000,
        )
        assert abs(cost - 3.0) < 0.001

    def test_haiku_45_input(self):
        # Haiku 4.5: 1M input at $1.00/1M
        cost = calculate_cost("claude-haiku-4-5", input_tokens=1_000_000)
        assert abs(cost - 1.0) < 0.001

    def test_haiku_35_legacy_input(self):
        # Haiku 3.5: 1M input at $0.80/1M
        cost = calculate_cost("claude-haiku-3-5", input_tokens=1_000_000)
        assert abs(cost - 0.80) < 0.001

    def test_unknown_model_uses_sonnet(self):
        cost = calculate_cost("unknown-model", input_tokens=1_000_000)
        expected = calculate_cost("claude-sonnet-4-6", input_tokens=1_000_000)
        assert abs(cost - expected) < 0.001
