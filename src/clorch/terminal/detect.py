"""Auto-detect the active terminal emulator and return the appropriate backend."""
from __future__ import annotations

import os
from functools import lru_cache

from clorch.terminal.backend import TerminalBackend


@lru_cache(maxsize=1)
def get_backend() -> TerminalBackend:
    """Return a ``TerminalBackend`` for the current terminal.

    Resolution order:

    1. ``CLORCH_TERMINAL`` env var — explicit override
       (``iterm``, ``apple_terminal``, ``ghostty``).
    2. ``TERM_PROGRAM`` env var — standard terminal identification.
    3. Fallback → ``GhosttyBackend`` (minimal: only ``bring_to_front``).
    """
    override = os.environ.get("CLORCH_TERMINAL", "").lower().strip()
    if override:
        return _backend_from_name(override)

    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program == "iTerm.app":
        from clorch.terminal.iterm import ITermBackend
        return ITermBackend()
    if term_program == "Apple_Terminal":
        from clorch.terminal.apple_terminal import AppleTerminalBackend
        return AppleTerminalBackend()
    if term_program == "ghostty":
        from clorch.terminal.ghostty import GhosttyBackend
        return GhosttyBackend()

    # Unknown terminal — use the minimal stub
    from clorch.terminal.ghostty import GhosttyBackend
    return GhosttyBackend()


def _backend_from_name(name: str) -> TerminalBackend:
    """Instantiate a backend by short name."""
    if name in ("iterm", "iterm2"):
        from clorch.terminal.iterm import ITermBackend
        return ITermBackend()
    if name in ("apple_terminal", "terminal", "terminal.app"):
        from clorch.terminal.apple_terminal import AppleTerminalBackend
        return AppleTerminalBackend()
    if name == "ghostty":
        from clorch.terminal.ghostty import GhosttyBackend
        return GhosttyBackend()

    # Unknown override — fall back to minimal stub
    from clorch.terminal.ghostty import GhosttyBackend
    return GhosttyBackend()
