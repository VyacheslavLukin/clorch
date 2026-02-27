"""Settings panel — toggle controls for TUI preferences."""
from __future__ import annotations

from textual.widgets import Static
from rich.text import Text

from clorch.constants import CYAN, GREEN, GREY


class SettingsPanel(Static):
    """Compact settings panel with toggle controls."""

    DEFAULT_CSS = """
    SettingsPanel {
        height: auto;
        max-height: 3;
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs) -> None:
        super().__init__("", **kwargs)
        self._sound_enabled = False

    @property
    def sound_enabled(self) -> bool:
        return self._sound_enabled

    def toggle_sound(self) -> bool:
        """Toggle sound and re-render. Returns new state."""
        self._sound_enabled = not self._sound_enabled
        self._refresh_content()
        return self._sound_enabled

    def on_mount(self) -> None:
        self._refresh_content()

    def _refresh_content(self) -> None:
        text = Text()
        text.append("[s]", style=f"bold {CYAN}")
        text.append(" Sound  ", style="white")
        if self._sound_enabled:
            text.append("ON", style=f"bold {GREEN}")
        else:
            text.append("OFF", style=f"dim {GREY}")
        self.update(text)
