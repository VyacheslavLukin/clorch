"""Styled header bar with Unicode separators, tmux session name, and counts."""
from __future__ import annotations

from textual.widgets import Static
from rich.text import Text

from clorch.state.models import StatusSummary
from clorch.constants import GREEN, RED, YELLOW, PINK, GREY, CYAN, BRAILLE_SPINNER


class HeaderBar(Static):
    """1-line header: CLORCH --- tmux:session --- counts --- N agents."""

    DEFAULT_CSS = """
    HeaderBar {
        height: 1;
        padding: 0 1;
        text-style: bold;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(Text(" CLORCH", style=f"bold {GREEN}"), **kwargs)
        self._tmux_session: str = ""
        self._anim_frame: int = 0
        self._summary: StatusSummary | None = None

    def set_tmux_session(self, name: str) -> None:
        """Set the tmux session name for display."""
        self._tmux_session = name

    def tick_animation(self, frame: int) -> None:
        """Advance animation frame and re-render if there are working agents."""
        self._anim_frame = frame
        if self._summary and self._summary.working > 0:
            self._refresh_display()

    def update_summary(self, summary: StatusSummary) -> None:
        self._summary = summary
        self._refresh_display()

    def _refresh_display(self) -> None:
        summary = self._summary
        if summary is None:
            return
        text = Text()

        # Branding
        text.append(" CLORCH", style=f"bold {GREEN}")
        text.append(" \u2500\u2500\u2500 ", style=f"dim {GREY}")

        # tmux session name (if available)
        if self._tmux_session:
            text.append(self._tmux_session, style=f"{CYAN}")
            text.append(" \u2500\u2500\u2500 ", style=f"dim {GREY}")

        # Status counts — full words
        if summary.working > 0:
            spinner = BRAILLE_SPINNER[self._anim_frame % len(BRAILLE_SPINNER)]
            text.append(f"{spinner} ", style=f"bold {GREEN}")
        text.append("Working: ", style="dim")
        text.append(str(summary.working), style=f"bold {GREEN}")
        text.append(" \u2502 ", style=f"dim {GREY}")

        text.append("Idle: ", style="dim")
        text.append(str(summary.idle), style=f"{GREY}")
        text.append(" \u2502 ", style=f"dim {GREY}")

        text.append("Perm: ", style="dim")
        text.append(str(summary.waiting_permission), style=f"bold {RED}")
        text.append(" \u2502 ", style=f"dim {GREY}")

        text.append("Ask: ", style="dim")
        text.append(str(summary.waiting_answer), style=f"bold {YELLOW}")
        text.append(" \u2502 ", style=f"dim {GREY}")

        text.append("Errors: ", style="dim")
        text.append(str(summary.error), style=f"bold {PINK}")

        # Agent total
        text.append(" \u2500\u2500\u2500 ", style=f"dim {GREY}")
        text.append(f"{summary.total} agents", style=f"bold {CYAN}")

        self.update(text)
