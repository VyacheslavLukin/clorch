"""Data models for Claude Code usage tracking."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TokenUsage:
    """Token counts for a session or aggregate."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0

    @property
    def total_input(self) -> int:
        """Total input tokens including cache write and read."""
        return self.input_tokens + self.cache_creation_input_tokens + self.cache_read_input_tokens

    def __iadd__(self, other: TokenUsage) -> TokenUsage:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_creation_input_tokens += other.cache_creation_input_tokens
        self.cache_read_input_tokens += other.cache_read_input_tokens
        return self


@dataclass
class SessionUsage:
    """Usage data for a single Claude Code session."""

    session_id: str = ""
    model: str = ""
    tokens: TokenUsage = field(default_factory=TokenUsage)
    message_count: int = 0
    cost: float = 0.0


@dataclass
class UsageSummary:
    """Aggregated usage across all sessions."""

    total_cost: float = 0.0
    total_input: int = 0
    total_output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    cache_hit_rate: float = 0.0
    burn_rate: float = 0.0
    message_count: int = 0
    session_count: int = 0
    sessions: dict[str, SessionUsage] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        """Input (excl. cache read) + output."""
        return self.total_input + self.total_output
