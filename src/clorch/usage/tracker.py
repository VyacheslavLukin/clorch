"""Usage tracker — aggregates JSONL session data with incremental parsing."""
from __future__ import annotations

import time
from collections import deque
from datetime import date, datetime, timezone

from clorch.usage.models import SessionUsage, UsageSummary
from clorch.usage.parser import iter_today_jsonl_files, parse_session_usage
from clorch.usage.pricing import calculate_cost


class UsageTracker:
    """Aggregates Claude Code usage data from JSONL session logs.

    - Active sessions: incremental parsing (byte offset) every poll.
    - All today-modified sessions: full scan every 60s.
    - Burn rate: rolling 10-minute cost history window.
    """

    def __init__(self) -> None:
        # byte offsets for incremental parsing: path_str -> offset
        self._offsets: dict[str, int] = {}
        # cached session usage: session_id -> SessionUsage
        self._sessions: dict[str, SessionUsage] = {}
        # slow scan timestamp
        self._last_full_scan: float = 0.0
        self._full_scan_interval: float = 60.0
        # burn rate: deque of (timestamp, total_cost)
        self._cost_history: deque[tuple[float, float]] = deque()
        self._burn_rate_window: float = 600.0  # 10 minutes
        # midnight rollover
        self._current_date: date | None = None

    def poll(self, active_session_paths: list[str] | None = None) -> UsageSummary:
        """Poll JSONL files and return aggregated usage summary.

        *active_session_paths*: list of JSONL file path strings for currently
        active sessions (fast incremental path). Pass None to skip.
        """
        now = time.monotonic()
        today = date.today()

        # Midnight rollover — reset everything
        if self._current_date is not None and today != self._current_date:
            self._offsets.clear()
            self._sessions.clear()
            self._cost_history.clear()
        self._current_date = today

        # Local midnight — "today" matches user's timezone
        today_local = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        today_start = today_local.astimezone(timezone.utc)

        # Fast path: incremental parsing of active sessions
        if active_session_paths:
            for path_str in active_session_paths:
                from pathlib import Path
                path = Path(path_str)
                if not path.exists():
                    continue
                offset = self._offsets.get(path_str, 0)
                usage, new_offset = parse_session_usage(path, since=today_start, byte_offset=offset)
                self._offsets[path_str] = new_offset
                if usage:
                    self._merge_session(usage)

        # Slow path: full scan of all today-modified JSONL files
        if now - self._last_full_scan >= self._full_scan_interval:
            self._last_full_scan = now
            for path in iter_today_jsonl_files():
                path_str = str(path)
                if path_str in self._offsets:
                    continue  # already tracked incrementally
                usage, new_offset = parse_session_usage(path, since=today_start)
                self._offsets[path_str] = new_offset
                if usage:
                    self._sessions[usage.session_id] = usage

        # Build summary
        summary = self._build_summary()

        # Update burn rate
        self._cost_history.append((time.monotonic(), summary.total_cost))
        self._prune_cost_history()
        summary.burn_rate = self._compute_burn_rate()

        return summary

    def _merge_session(self, usage: SessionUsage) -> None:
        """Merge incremental usage into cached session data."""
        existing = self._sessions.get(usage.session_id)
        if existing is None:
            self._sessions[usage.session_id] = usage
        else:
            existing.tokens += usage.tokens
            existing.message_count += usage.message_count
            if usage.model:
                existing.model = usage.model

    def _build_summary(self) -> UsageSummary:
        """Build aggregate summary from all cached sessions."""
        total_cost = 0.0
        total_input = 0
        total_output = 0
        cache_read = 0
        cache_write = 0
        message_count = 0

        sessions: dict[str, SessionUsage] = {}
        for sid, su in self._sessions.items():
            cost = calculate_cost(
                su.model,
                input_tokens=su.tokens.input_tokens,
                output_tokens=su.tokens.output_tokens,
                cache_write_tokens=su.tokens.cache_creation_input_tokens,
                cache_read_tokens=su.tokens.cache_read_input_tokens,
            )
            su.cost = cost
            total_cost += cost
            total_input += su.tokens.input_tokens + su.tokens.cache_creation_input_tokens
            total_output += su.tokens.output_tokens
            cache_read += su.tokens.cache_read_input_tokens
            cache_write += su.tokens.cache_creation_input_tokens
            message_count += su.message_count
            sessions[sid] = su

        # Cache hit rate: cache_read / (cache_read + cache_write + input)
        total_cache_eligible = cache_read + cache_write + sum(
            s.tokens.input_tokens for s in self._sessions.values()
        )
        if total_cache_eligible > 0:
            cache_hit_rate = cache_read / total_cache_eligible * 100
        else:
            cache_hit_rate = 0.0

        return UsageSummary(
            total_cost=total_cost,
            total_input=total_input,
            total_output=total_output,
            cache_read=cache_read,
            cache_write=cache_write,
            cache_hit_rate=cache_hit_rate,
            message_count=message_count,
            session_count=len(sessions),
            sessions=sessions,
        )

    def _prune_cost_history(self) -> None:
        """Remove entries older than the burn rate window."""
        cutoff = time.monotonic() - self._burn_rate_window
        while self._cost_history and self._cost_history[0][0] < cutoff:
            self._cost_history.popleft()

    def _compute_burn_rate(self) -> float:
        """Compute $/hr burn rate from the rolling cost history window."""
        if len(self._cost_history) < 2:
            return 0.0
        oldest_time, oldest_cost = self._cost_history[0]
        newest_time, newest_cost = self._cost_history[-1]
        elapsed = newest_time - oldest_time
        if elapsed < 10.0:  # need at least 10s of data
            return 0.0
        cost_delta = newest_cost - oldest_cost
        return max(0.0, cost_delta / elapsed * 3600)
