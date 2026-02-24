"""Agent detail panel — structured key-value display in the sidebar."""
from __future__ import annotations

from textual.widgets import Static
from rich.text import Text

from clorch.state.models import AgentState
from clorch.constants import (
    STATUS_DISPLAY, SPARKLINE_CHARS,
    CYAN, GREEN, GREY, PINK, RED, YELLOW,
)

# Label column width for alignment
_LABEL_W = 12


class AgentDetail(Static):
    """Shows detailed information about the selected agent.

    Structured key-value layout with semantic colors, extended sparkline,
    and recent tools breadcrumb.
    """

    DEFAULT_CSS = """
    AgentDetail {
        height: auto;
        max-height: 16;
        border: solid;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._agent: AgentState | None = None

    def show_agent(self, agent: AgentState | None) -> None:
        self._agent = agent
        if agent is None:
            self.update("")
            return

        symbol, label, color = STATUS_DISPLAY[agent.status]

        text = Text()

        # Title line
        text.append("DETAIL", style=f"bold {CYAN}")
        text.append("  ", style="dim")
        text.append(agent.project_name or agent.session_id[:12], style="bold white")
        text.append("\n")

        # Status + Uptime
        text.append(f"{'Status':<{_LABEL_W}s}", style=f"dim {GREY}")
        text.append(f"{symbol} {label}", style=f"bold {color}")
        text.append("    ", style="dim")
        text.append(f"{'Uptime':<8s}", style=f"dim {GREY}")
        text.append(f"{agent.uptime}", style="white")
        text.append("\n")

        # Path
        if agent.cwd:
            # Shorten home directory
            path = agent.cwd.replace("/Users/", "~/", 1)
            if path.startswith("~/"):
                # Further shorten: ~/username/... -> ~/...
                parts = path.split("/", 2)
                if len(parts) >= 3:
                    path = "~/" + parts[2]
            text.append(f"{'Path':<{_LABEL_W}s}", style=f"dim {GREY}")
            text.append(f"{path}", style=GREEN)
            text.append("\n")

        # Model + Last tool
        text.append(f"{'Model':<{_LABEL_W}s}", style=f"dim {GREY}")
        text.append(f"{agent.model or '-'}", style=CYAN)
        if agent.last_tool:
            text.append("    ", style="dim")
            text.append(f"{'Last tool':<10s}", style=f"dim {GREY}")
            text.append(f"{agent.last_tool}", style="white")
        text.append("\n")

        # Counts line: Tools, Errors, Subagents, Compacts, Tasks
        text.append(f"{'Tools':<{_LABEL_W}s}", style=f"dim {GREY}")
        text.append(f"{agent.tool_count}", style="white")
        text.append("    ", style="dim")
        text.append("Errors ", style=f"dim {GREY}")
        text.append(
            f"{agent.error_count}",
            style=f"bold {PINK}" if agent.error_count else f"dim {GREY}",
        )
        if agent.subagent_count:
            text.append("    ", style="dim")
            text.append("Subs ", style=f"dim {GREY}")
            text.append(f"{agent.subagent_count}", style=CYAN)
        if agent.compact_count:
            text.append("    ", style="dim")
            text.append("Compacts ", style=f"dim {GREY}")
            text.append(f"{agent.compact_count}", style=PINK)
        if agent.task_completed_count:
            text.append("    ", style="dim")
            text.append("Tasks ", style=f"dim {GREY}")
            text.append(f"{agent.task_completed_count}", style=GREEN)
        text.append("\n")

        # Extended sparkline (use all available history, up to 20 chars)
        text.append(f"{'Activity':<{_LABEL_W}s}", style=f"dim {GREY}")
        sparkline = self._render_extended_sparkline(agent.activity_history)
        text.append_text(sparkline)
        text.append("\n")

        # Notification message
        if agent.notification_message:
            text.append(f"{'Msg':<{_LABEL_W}s}", style=f"dim {GREY}")
            msg = agent.notification_message
            if len(msg) > 80:
                msg = msg[:78] + ".."
            text.append(f'"{msg}"', style=f"italic {YELLOW}")

        self.update(text)

    @staticmethod
    def _render_extended_sparkline(history: list[int]) -> Text:
        """Render an extended sparkline (up to 20 chars)."""
        # Use up to 20 most recent data points
        recent = history[-20:] if len(history) >= 20 else history
        if not recent or max(recent) == 0:
            return Text("\u2581" * min(len(recent), 20), style=f"dim {GREY}")
        max_val = max(recent)
        chars = []
        for v in recent:
            idx = min(int(v / max(max_val, 1) * 7), 7)
            chars.append(SPARKLINE_CHARS[idx])
        return Text("".join(chars), style=CYAN)
