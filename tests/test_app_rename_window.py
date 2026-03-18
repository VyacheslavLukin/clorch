"""Tests for OrchestratorApp._rename_selected_window."""
from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestRenameSelectedWindow:
    """Unit tests for _rename_selected_window without a running Textual app.

    Uses object.__new__ to bypass __init__ and calls the method directly,
    mocking out tmux and SessionList dependencies.
    """

    def _make_app(self):
        from clorch.tui.app import OrchestratorApp

        return object.__new__(OrchestratorApp)

    def _make_agent(self, project_name: str = "myproject") -> MagicMock:
        agent = MagicMock()
        agent.project_name = project_name
        return agent

    # ------------------------------------------------------------------
    # Guard: no tmux
    # ------------------------------------------------------------------

    def test_no_tmux_returns_early(self):
        """Returns early (no notify, no push_screen) when tmux is unavailable."""
        app = self._make_app()
        app._get_tmux = MagicMock(return_value=None)
        app.notify = MagicMock()
        app.push_screen = MagicMock()

        app._rename_selected_window()

        app.notify.assert_not_called()
        app.push_screen.assert_not_called()

    # ------------------------------------------------------------------
    # Guard: no agent selected
    # ------------------------------------------------------------------

    def test_no_agent_selected_notifies(self):
        """Notifies with warning when no agent is selected."""
        app = self._make_app()
        tmux = MagicMock()
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()
        app.push_screen = MagicMock()

        session_list = MagicMock()
        session_list.get_selected_agent.return_value = None
        app.query_one = MagicMock(return_value=session_list)

        app._rename_selected_window()

        app.notify.assert_called_once_with("No agent selected", severity="warning")
        app.push_screen.assert_not_called()

    # ------------------------------------------------------------------
    # Guard: no tmux window mapped
    # ------------------------------------------------------------------

    def test_no_tmux_window_notifies(self):
        """Notifies with warning when agent has no mapped tmux window."""
        app = self._make_app()
        tmux = MagicMock()
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()
        app.push_screen = MagicMock()

        agent = self._make_agent("myproject")
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value=None):
            app._rename_selected_window()

        app.notify.assert_called_once_with("No tmux window for myproject", severity="warning")
        app.push_screen.assert_not_called()

    # ------------------------------------------------------------------
    # Prompt cancelled
    # ------------------------------------------------------------------

    def test_prompt_cancelled_no_rename(self):
        """Does not call rename_window when prompt is cancelled (None result)."""
        app = self._make_app()
        tmux = MagicMock()
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()

        agent = self._make_agent()
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        captured_callback = {}

        def fake_push_screen(screen, callback=None):
            captured_callback["fn"] = callback

        app.push_screen = fake_push_screen

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value="mywin"):
            app._rename_selected_window()

        # Simulate user cancelling the prompt
        captured_callback["fn"](None)

        tmux.rename_window.assert_not_called()
        app.notify.assert_not_called()

    def test_prompt_empty_string_no_rename(self):
        """Does not call rename_window when prompt returns empty string."""
        app = self._make_app()
        tmux = MagicMock()
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()

        agent = self._make_agent()
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        captured_callback = {}

        def fake_push_screen(screen, callback=None):
            captured_callback["fn"] = callback

        app.push_screen = fake_push_screen

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value="mywin"):
            app._rename_selected_window()

        captured_callback["fn"]("")

        tmux.rename_window.assert_not_called()
        app.notify.assert_not_called()

    # ------------------------------------------------------------------
    # Rename succeeds
    # ------------------------------------------------------------------

    def test_rename_success_notifies(self):
        """Notifies with success message when rename_window returns True."""
        app = self._make_app()
        tmux = MagicMock()
        tmux.rename_window.return_value = True
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()

        agent = self._make_agent()
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        captured_callback = {}

        def fake_push_screen(screen, callback=None):
            captured_callback["fn"] = callback

        app.push_screen = fake_push_screen

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value="mywin"):
            app._rename_selected_window()

        captured_callback["fn"]("shiny-new")

        tmux.rename_window.assert_called_once_with("mywin", "shiny-new")
        app.notify.assert_called_once_with("Renamed to 'shiny-new'")

    # ------------------------------------------------------------------
    # Rename fails
    # ------------------------------------------------------------------

    def test_rename_failure_notifies_error(self):
        """Notifies with error severity when rename_window returns False."""
        app = self._make_app()
        tmux = MagicMock()
        tmux.rename_window.return_value = False
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()

        agent = self._make_agent()
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        captured_callback = {}

        def fake_push_screen(screen, callback=None):
            captured_callback["fn"] = callback

        app.push_screen = fake_push_screen

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value="mywin"):
            app._rename_selected_window()

        captured_callback["fn"]("badname")

        tmux.rename_window.assert_called_once_with("mywin", "badname")
        app.notify.assert_called_once_with("Rename failed", severity="error")

    # ------------------------------------------------------------------
    # PromptScreen pre-filled with current window name
    # ------------------------------------------------------------------

    def test_prompt_screen_placeholder_is_window_name(self):
        """PromptScreen is opened with the current window name as placeholder."""
        from clorch.tui.app import PromptScreen

        app = self._make_app()
        tmux = MagicMock()
        app._get_tmux = MagicMock(return_value=tmux)
        app.notify = MagicMock()

        agent = self._make_agent()
        session_list = MagicMock()
        session_list.get_selected_agent.return_value = agent
        app.query_one = MagicMock(return_value=session_list)

        pushed_screens = []

        def fake_push_screen(screen, callback=None):
            pushed_screens.append(screen)

        app.push_screen = fake_push_screen

        with patch("clorch.tmux.navigator.map_agent_to_window", return_value="cobra"):
            app._rename_selected_window()

        assert len(pushed_screens) == 1
        screen = pushed_screens[0]
        assert isinstance(screen, PromptScreen)
        assert screen._placeholder == "cobra"
