"""Tests for tmux pane detection parsing in event_handler.sh.

Validates that the |||‑delimited tmux list-panes parsing correctly
extracts window name, pane index, and session name — including when
names contain spaces.
"""
from __future__ import annotations

import subprocess

import pytest


def _run_tmux_parse(pane_listing: str, target_tty: str) -> dict[str, str]:
    """Feed *pane_listing* through the same awk+read logic used in event_handler.sh.

    Returns a dict with keys ``window``, ``pane``, ``session``.
    """
    script = f"""\
_CLAUDE_TTY="{target_tty}"
TMUX_WINDOW=""
TMUX_PANE=""
TMUX_SESSION=""
_TMUX_INFO="$(printf '%b' '{pane_listing}' \\
    | awk -v tty="/dev/$_CLAUDE_TTY" -F '\\\\|\\\\|\\\\|' '$1 == tty {{ print $2; print $3; print $4; exit }}')" || true
if [[ -n "$_TMUX_INFO" ]]; then
    {{ read -r TMUX_WINDOW; read -r TMUX_PANE; read -r TMUX_SESSION; }} <<< "$_TMUX_INFO"
fi
echo "$TMUX_WINDOW"
echo "$TMUX_PANE"
echo "$TMUX_SESSION"
"""
    result = subprocess.run(
        ["bash", "-c", script],
        capture_output=True, text=True, timeout=5,
    )
    lines = result.stdout.strip().split("\n")
    # Pad to 3 lines if output is short
    while len(lines) < 3:
        lines.append("")
    return {"window": lines[0], "pane": lines[1], "session": lines[2]}


class TestTmuxParsing:
    """Verify the |||‑delimited tmux parsing logic."""

    def test_simple_names(self):
        """Standard names without spaces parse correctly."""
        listing = "/dev/ttys035|||swift-core|||1|||meta"
        result = _run_tmux_parse(listing, "ttys035")
        assert result == {"window": "swift-core", "pane": "1", "session": "meta"}

    def test_window_name_with_spaces(self):
        """Window names containing spaces are preserved."""
        listing = "/dev/ttys010|||my project|||0|||work"
        result = _run_tmux_parse(listing, "ttys010")
        assert result == {"window": "my project", "pane": "0", "session": "work"}

    def test_session_name_with_spaces(self):
        """Session names containing spaces are preserved."""
        listing = "/dev/ttys010|||editor|||2|||work session"
        result = _run_tmux_parse(listing, "ttys010")
        assert result == {"window": "editor", "pane": "2", "session": "work session"}

    def test_both_names_with_spaces(self):
        """Both window and session names can contain spaces."""
        listing = "/dev/ttys010|||my project|||0|||work session"
        result = _run_tmux_parse(listing, "ttys010")
        assert result == {"window": "my project", "pane": "0", "session": "work session"}

    def test_multiple_panes_selects_matching_tty(self):
        """Only the pane matching the target tty is returned."""
        listing = (
            "/dev/ttys001|||other|||0|||sess\\n"
            "/dev/ttys010|||target|||1|||main\\n"
            "/dev/ttys020|||another|||2|||main"
        )
        result = _run_tmux_parse(listing, "ttys010")
        assert result == {"window": "target", "pane": "1", "session": "main"}

    def test_no_matching_tty(self):
        """Non-matching tty returns empty fields."""
        listing = "/dev/ttys001|||editor|||0|||work"
        result = _run_tmux_parse(listing, "ttys999")
        assert result == {"window": "", "pane": "", "session": ""}

    def test_empty_listing(self):
        """Empty pane listing returns empty fields."""
        result = _run_tmux_parse("", "ttys010")
        assert result == {"window": "", "pane": "", "session": ""}
