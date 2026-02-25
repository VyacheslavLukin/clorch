"""Tests for terminal backend auto-detection."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from clorch.terminal.detect import get_backend, _backend_from_name
from clorch.terminal.iterm import ITermBackend
from clorch.terminal.apple_terminal import AppleTerminalBackend
from clorch.terminal.ghostty import GhosttyBackend


class TestGetBackend:
    """Tests for get_backend() auto-detection."""

    def setup_method(self):
        # Clear the lru_cache between tests
        get_backend.cache_clear()

    def teardown_method(self):
        get_backend.cache_clear()

    def test_iterm_detected(self):
        with patch.dict("os.environ", {"TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, ITermBackend)

    def test_apple_terminal_detected(self):
        with patch.dict("os.environ", {"TERM_PROGRAM": "Apple_Terminal"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, AppleTerminalBackend)

    def test_ghostty_detected(self):
        with patch.dict("os.environ", {"TERM_PROGRAM": "ghostty"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)

    def test_unknown_terminal_falls_back_to_ghostty(self):
        with patch.dict("os.environ", {"TERM_PROGRAM": "alacritty"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)

    def test_empty_term_program_falls_back_to_ghostty(self):
        env = {"TERM_PROGRAM": ""}
        with patch.dict("os.environ", env, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)

    def test_override_iterm(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "iterm", "TERM_PROGRAM": "ghostty"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, ITermBackend)

    def test_override_iterm2(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "iterm2", "TERM_PROGRAM": "ghostty"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, ITermBackend)

    def test_override_apple_terminal(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "apple_terminal", "TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, AppleTerminalBackend)

    def test_override_terminal(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "terminal", "TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, AppleTerminalBackend)

    def test_override_terminal_app(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "terminal.app", "TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, AppleTerminalBackend)

    def test_override_ghostty(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "ghostty", "TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)

    def test_override_unknown_falls_back_to_ghostty(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "wezterm", "TERM_PROGRAM": "iTerm.app"}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)

    def test_override_case_insensitive(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "ITERM", "TERM_PROGRAM": ""}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, ITermBackend)

    def test_override_whitespace_stripped(self):
        with patch.dict("os.environ", {"CLORCH_TERMINAL": "  iterm  ", "TERM_PROGRAM": ""}, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, ITermBackend)

    def test_no_env_vars_falls_back_to_ghostty(self):
        env = {"TERM_PROGRAM": "", "CLORCH_TERMINAL": ""}
        with patch.dict("os.environ", env, clear=False):
            get_backend.cache_clear()
            backend = get_backend()
        assert isinstance(backend, GhosttyBackend)


class TestBackendFromName:
    """Tests for _backend_from_name() helper."""

    def test_iterm(self):
        assert isinstance(_backend_from_name("iterm"), ITermBackend)

    def test_iterm2(self):
        assert isinstance(_backend_from_name("iterm2"), ITermBackend)

    def test_apple_terminal(self):
        assert isinstance(_backend_from_name("apple_terminal"), AppleTerminalBackend)

    def test_terminal(self):
        assert isinstance(_backend_from_name("terminal"), AppleTerminalBackend)

    def test_terminal_app(self):
        assert isinstance(_backend_from_name("terminal.app"), AppleTerminalBackend)

    def test_ghostty(self):
        assert isinstance(_backend_from_name("ghostty"), GhosttyBackend)

    def test_unknown(self):
        assert isinstance(_backend_from_name("kitty"), GhosttyBackend)
