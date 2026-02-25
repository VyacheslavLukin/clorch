"""Multi-terminal backend support (iTerm2, Terminal.app, Ghostty)."""
from clorch.terminal.backend import TerminalBackend
from clorch.terminal.detect import get_backend

__all__ = ["TerminalBackend", "get_backend"]
