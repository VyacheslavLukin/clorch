"""In-process sound alerts for the TUI (macOS only)."""
from __future__ import annotations

import subprocess
import sys

from clorch.constants import AgentStatus

# Map attention statuses to macOS system sound files
_STATUS_SOUNDS: dict[AgentStatus, str] = {
    AgentStatus.WAITING_PERMISSION: "/System/Library/Sounds/Sosumi.aiff",
    AgentStatus.WAITING_ANSWER: "/System/Library/Sounds/Ping.aiff",
    AgentStatus.ERROR: "/System/Library/Sounds/Basso.aiff",
}


def play_status_sound(status: AgentStatus) -> None:
    """Play a system sound for an attention status (non-blocking)."""
    if sys.platform != "darwin":
        return
    path = _STATUS_SOUNDS.get(status)
    if not path:
        return
    try:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        pass
