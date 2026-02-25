"""Event log panel — streaming event log from all agents."""
from __future__ import annotations

from datetime import datetime, timezone

from textual.widgets import RichLog
from rich.text import Text

from clorch.constants import GREY


class EventLog(RichLog):
    """Scrolling event log with colored entries."""

    def __init__(self, **kwargs) -> None:
        super().__init__(max_lines=200, auto_scroll=True, markup=False, wrap=True, **kwargs)

    def write_event(
        self,
        agent_name: str,
        icon: str,
        message: str,
        color: str,
    ) -> None:
        now = datetime.now(timezone.utc).strftime("%H:%M:%S")
        text = Text()
        text.append(now, style=f"dim {GREY}")
        text.append("  ")
        text.append(f"{agent_name:<12s}", style="white")
        text.append("  ")
        text.append(icon, style=color)
        text.append(" ")
        text.append(message, style=color)
        self.write(text)
