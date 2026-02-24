"""Action panel widget — sidebar panel showing attention items.

This is the wide-mode replacement for ActionQueue.  In the new layout it
lives in the right sidebar below AgentDetail.  A full implementation will
come in Phase 3; this file provides the same public API as ActionQueue so
the app can use it as a drop-in during the layout transition.
"""
from __future__ import annotations

from textual.widget import Widget
from rich.text import Text

from clorch.state.models import ActionItem
from clorch.constants import RED, YELLOW, PINK, CYAN, GREEN, GREY


class ActionPanel(Widget):
    """Renders attention items in the sidebar action panel.

    Hidden when no actions are present.
    """

    DEFAULT_CSS = """
    ActionPanel {
        height: auto;
        max-height: 12;
        padding: 0 1;
    }
    ActionPanel.hidden {
        display: none;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._items: list[ActionItem] = []
        self._focused_letter: str | None = None

    def update_actions(self, items: list[ActionItem]) -> None:
        """Replace the action list and toggle visibility."""
        self._items = items
        if self._focused_letter:
            if not any(i.letter == self._focused_letter for i in items):
                self._focused_letter = None
        if items:
            self.remove_class("hidden")
        else:
            self.add_class("hidden")
        self.refresh()

    def set_focus(self, letter: str) -> None:
        """Focus an action by its assigned letter."""
        self._focused_letter = letter
        self.refresh()

    def clear_focus(self) -> None:
        """Clear the focused action."""
        self._focused_letter = None
        self.refresh()

    @property
    def focused_letter(self) -> str | None:
        return self._focused_letter

    def get_action(self, letter: str) -> ActionItem | None:
        """Look up an action by its assigned letter."""
        for item in self._items:
            if item.letter == letter:
                return item
        return None

    @property
    def has_approvable(self) -> bool:
        """True if any action is approvable (PERM status)."""
        return any(item.actionable for item in self._items)

    def render(self) -> Text:
        if not self._items:
            return Text("")

        text = Text()

        # Header
        count = len(self._items)
        text.append("ACTIONS", style=f"bold {CYAN}")
        text.append(f" ({count})", style=f"dim {GREY}")
        if self.has_approvable:
            text.append("  ")
            text.append("[Y]", style=f"bold {GREEN}")
            text.append(" all", style="dim")
        text.append("\n")

        for item in self._items:
            is_focused = self._focused_letter == item.letter

            # Determine type and color
            if item.actionable:
                symbol = "[!]"
                color = RED
            elif item.agent.status.value == "WAITING_ANSWER":
                symbol = "[?]"
                color = YELLOW
            else:
                symbol = "[X]"
                color = PINK

            # Left accent for PERM
            if item.actionable:
                text.append("\u2503 ", style=f"bold {RED}")
            else:
                text.append("  ", style="dim")

            # Letter badge
            letter_style = f"bold {GREEN}" if is_focused else f"bold {CYAN}"
            text.append(f"[{item.letter}]", style=letter_style)
            text.append(" ", style="dim")

            # Symbol
            text.append(f"{symbol} ", style=f"bold {color}")

            # Project name
            project = item.agent.project_name or item.agent.session_id[:12]
            text.append(f"{project}", style="bold white")
            text.append("\n")

            # Summary line
            summary = item.summary or ""
            if is_focused and item.actionable:
                # Full message + approval controls
                text.append(f'  "{summary}"', style="italic")
                text.append("\n")
                text.append("  >>> ", style=f"bold {GREEN}")
                text.append("[y]", style=f"bold reverse {GREEN}")
                text.append(" approve  ", style="dim")
                text.append("[n]", style=f"bold reverse {RED}")
                text.append(" deny  ", style="dim")
                text.append("[Esc]", style=f"bold {CYAN}")
                text.append(" cancel", style="dim")
                text.append("\n")
            else:
                trunc = summary[:60] if summary else ""
                if trunc:
                    text.append(f'  "{trunc}"', style="dim italic")
                if item.actionable:
                    text.append("  ")
                    text.append("[y]", style=f"bold {GREEN}")
                    text.append("[n]", style=f"bold {RED}")
                else:
                    text.append("  ")
                    text.append("[->]", style=f"bold {CYAN}")
                text.append("\n")

        return text
