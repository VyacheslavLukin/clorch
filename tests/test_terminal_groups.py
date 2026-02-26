"""Tests for terminal group separation in the session list."""
from __future__ import annotations

import pytest

from clorch.constants import AgentStatus
from clorch.state.models import AgentState
from clorch.tui.widgets.session_list import (
    _agent_terminal_group,
    _group_sort_key,
    SessionList,
)


class TestAgentTerminalGroup:
    """Tests for _agent_terminal_group() helper."""

    def test_tmux_window_overrides_term_program(self):
        """Agent with tmux_window is grouped as 'tmux' regardless of term_program."""
        agent = AgentState(
            session_id="a1",
            tmux_window="backend",
            term_program="iTerm.app",
        )
        assert _agent_terminal_group(agent) == "tmux"

    def test_iterm_agent(self):
        agent = AgentState(session_id="a1", term_program="iTerm.app")
        assert _agent_terminal_group(agent) == "iTerm"

    def test_ghostty_agent(self):
        agent = AgentState(session_id="a1", term_program="ghostty")
        assert _agent_terminal_group(agent) == "Ghostty"

    def test_empty_term_program(self):
        agent = AgentState(session_id="a1", term_program="")
        assert _agent_terminal_group(agent) == "unknown"

    def test_unknown_term_program_passthrough(self):
        agent = AgentState(session_id="a1", term_program="wezterm")
        assert _agent_terminal_group(agent) == "wezterm"


class TestGroupSortKey:
    """Tests for _group_sort_key() sort ordering."""

    def test_local_first(self):
        """Local terminal group sorts before everything."""
        key = _group_sort_key("iTerm", "iTerm")
        assert key == (0, "iTerm")

    def test_tmux_second(self):
        """tmux sorts after local but before others."""
        key = _group_sort_key("tmux", "iTerm")
        assert key == (1, "tmux")

    def test_other_last(self):
        """Non-local, non-tmux groups sort last."""
        key = _group_sort_key("Ghostty", "iTerm")
        assert key == (2, "Ghostty")

    def test_sort_order(self):
        """Full sort order: local < tmux < others alphabetical."""
        groups = ["Ghostty", "tmux", "iTerm", "wezterm"]
        local = "iTerm"
        sorted_groups = sorted(groups, key=lambda g: _group_sort_key(g, local))
        assert sorted_groups == ["iTerm", "tmux", "Ghostty", "wezterm"]


class TestSessionListGrouping:
    """Tests for SessionList._group_agents() logic."""

    def _make_list(self, local: str = "iTerm", can_resolve: bool = True) -> SessionList:
        """Create a SessionList with a specific local terminal."""
        sl = SessionList.__new__(SessionList)
        sl._local_terminal = local
        sl._backend_can_resolve = can_resolve
        return sl

    def test_single_group_no_separator(self):
        """When all agents are in the same group, no separators are added."""
        sl = self._make_list("iTerm")
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program="iTerm.app"),
            AgentState(session_id="a2", project_name="beta", term_program="iTerm.app"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        assert len(ordered) == 2
        assert len(separators) == 0
        assert child_map == [0, 1]
        assert dim_flags == [False, False]

    def test_two_groups_with_separators(self):
        """Two terminal groups produce separator rows."""
        sl = self._make_list("iTerm")
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program="iTerm.app"),
            AgentState(session_id="a2", project_name="beta", term_program="ghostty"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        # 2 separators + 2 agents = 4 children
        assert len(child_map) == 4
        assert len(separators) == 2
        # First separator is local group
        assert "local" in separators[0][1]
        assert separators[0][0] == 0  # child index 0
        # First agent (iTerm) at child index 1
        assert child_map[1] == 0
        # Ghostty agents are dimmed
        assert dim_flags[1] is True  # Ghostty agent

    def test_local_group_first(self):
        """Local terminal group comes first in the ordering."""
        sl = self._make_list("Ghostty")
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program="iTerm.app"),
            AgentState(session_id="a2", project_name="beta", term_program="ghostty"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        # First agent in the ordered list should be the Ghostty one (local)
        assert ordered[0].session_id == "a2"
        assert ordered[1].session_id == "a1"

    def test_tmux_agents_reachable(self):
        """Agents in tmux are always reachable (not dimmed)."""
        sl = self._make_list("iTerm")
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program="iTerm.app", tmux_window="backend"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        assert dim_flags[0] is False

    def test_tmux_after_local_before_others(self):
        """tmux group sorts between local and remote groups."""
        sl = self._make_list("iTerm")
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program="ghostty"),
            AgentState(session_id="a2", project_name="beta", term_program="iTerm.app", tmux_window="win"),
            AgentState(session_id="a3", project_name="gamma", term_program="iTerm.app"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        # Order: iTerm (local) → tmux → Ghostty
        assert ordered[0].session_id == "a3"  # iTerm (local)
        assert ordered[1].session_id == "a2"  # tmux
        assert ordered[2].session_id == "a1"  # Ghostty (remote)

    def test_alphabetical_within_group(self):
        """Agents within a group are sorted alphabetically by project name."""
        sl = self._make_list("iTerm")
        agents = [
            AgentState(session_id="a1", project_name="zebra", term_program="iTerm.app"),
            AgentState(session_id="a2", project_name="alpha", term_program="iTerm.app"),
            AgentState(session_id="a3", project_name="middle", term_program="iTerm.app"),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)

        assert [a.project_name for a in ordered] == ["alpha", "middle", "zebra"]

    def test_unknown_agents_not_dimmed_when_backend_resolves(self):
        """In iTerm (can_resolve=True), unknown agents are not dimmed."""
        sl = self._make_list("iTerm", can_resolve=True)
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program=""),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)
        assert dim_flags[0] is False

    def test_unknown_agents_dimmed_when_backend_cannot_resolve(self):
        """In Ghostty (can_resolve=False), unknown agents are dimmed."""
        sl = self._make_list("Ghostty", can_resolve=False)
        agents = [
            AgentState(session_id="a1", project_name="alpha", term_program=""),
        ]
        ordered, child_map, dim_flags, separators = sl._group_agents(agents)
        assert dim_flags[0] is True


class TestSessionListReachability:
    """Tests for is_agent_reachable()."""

    def _make_list(self, local: str = "iTerm", can_resolve: bool = True) -> SessionList:
        sl = SessionList.__new__(SessionList)
        sl._local_terminal = local
        sl._backend_can_resolve = can_resolve
        return sl

    def test_local_agent_reachable(self):
        sl = self._make_list("iTerm")
        agent = AgentState(session_id="a1", term_program="iTerm.app")
        assert sl.is_agent_reachable(agent) is True

    def test_tmux_agent_reachable(self):
        sl = self._make_list("iTerm")
        agent = AgentState(session_id="a1", term_program="ghostty", tmux_window="win")
        assert sl.is_agent_reachable(agent) is True

    def test_remote_agent_unreachable(self):
        sl = self._make_list("iTerm")
        agent = AgentState(session_id="a1", term_program="ghostty")
        assert sl.is_agent_reachable(agent) is False

    def test_unknown_reachable_when_backend_resolves(self):
        """In iTerm (can_resolve=True), unknown agents are reachable."""
        sl = self._make_list("iTerm", can_resolve=True)
        agent = AgentState(session_id="a1", term_program="")
        assert sl.is_agent_reachable(agent) is True

    def test_unknown_unreachable_when_backend_cannot_resolve(self):
        """In Ghostty (can_resolve=False), unknown agents are NOT reachable."""
        sl = self._make_list("Ghostty", can_resolve=False)
        agent = AgentState(session_id="a1", term_program="")
        assert sl.is_agent_reachable(agent) is False

    def test_tmux_always_reachable_even_without_resolve(self):
        """tmux agents reachable even from Ghostty."""
        sl = self._make_list("Ghostty", can_resolve=False)
        agent = AgentState(session_id="a1", term_program="iTerm.app", tmux_window="win")
        assert sl.is_agent_reachable(agent) is True
