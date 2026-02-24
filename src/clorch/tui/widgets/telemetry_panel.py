"""Telemetry panel — per-agent context gauge + activity sparkline."""
from __future__ import annotations

from textual.widgets import Static
from rich.text import Text

from clorch.state.models import AgentState
from clorch.constants import SPARKLINE_CHARS, TELEMETRY_HISTORY_LEN, CYAN, GREEN, GREY, RED, YELLOW


# Gauge bar width
_GAUGE_W = 8
# Sparkline width
_SPARKLINE_W = 15
# Agent name column width
_NAME_W = 12


class TelemetryPanel(Static):
    """Displays gauge bars and sparklines for all agents."""

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)

    def update_agents(
        self,
        agents: list[AgentState],
        selected_id: str | None,
        history_map: dict[str, list[int]],
    ) -> None:
        if not agents:
            self.update("")
            return

        text = Text()
        for i, agent in enumerate(agents):
            if i > 0:
                text.append("\n")

            # Agent name (highlighted if selected)
            name = (agent.project_name or agent.session_id[:_NAME_W])[:_NAME_W]
            is_selected = agent.session_id == selected_id
            name_style = "bold white" if is_selected else f"dim {GREY}"
            text.append(f"{name:<{_NAME_W}s}", style=name_style)
            text.append(" ")

            # Gauge bar from compact_count: 0=empty, 5+=full
            cc = agent.compact_count
            filled = min(cc, _GAUGE_W)
            if cc <= 1:
                bar_color = GREEN
            elif cc <= 3:
                bar_color = YELLOW
            else:
                bar_color = RED

            bar = "\u2588" * filled + "\u2591" * (_GAUGE_W - filled)
            text.append("[", style=f"dim {GREY}")
            text.append(bar, style=bar_color)
            text.append("]", style=f"dim {GREY}")
            text.append(f" {cc}c", style=f"dim {GREY}")
            text.append("  ")

            # Sparkline from extended history
            hist = history_map.get(agent.session_id, [])
            recent = hist[-_SPARKLINE_W:] if len(hist) >= _SPARKLINE_W else hist
            if not recent or max(recent) == 0:
                spark = "\u2581" * min(len(recent) or 1, _SPARKLINE_W)
                text.append(spark, style=f"dim {GREY}")
            else:
                max_val = max(recent)
                chars = []
                for v in recent:
                    idx = min(int(v / max(max_val, 1) * 7), 7)
                    chars.append(SPARKLINE_CHARS[idx])
                text.append("".join(chars), style=CYAN)

            # Warning icon at 4+ compacts
            if cc >= 4:
                text.append(" \u26a0", style=f"bold {RED}")

        self.update(text)
