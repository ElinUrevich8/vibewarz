"""Bot — the base class a vibecoder subclasses to write a bot.

Override `act(state)` and (optionally) `on_start` / `on_end`.

`act` may return either an action dict OR a tuple `(action, reasoning_text)`
— the reasoning is stored on the replay so viewers see what your bot was
thinking on each tick.
"""

from __future__ import annotations

from typing import Any

from .protocol import MatchPlayer


class Bot:
    """Subclass me and override `act(state)`."""

    game: str = ""  # subclasses set this, e.g. "curve"

    # Populated by the runner before the first act() call.
    seat: int = -1
    match_id: str | None = None
    players: list[MatchPlayer] | None = None

    def on_start(self, initial_state: dict[str, Any]) -> None:
        """Called once at game_start."""

    def act(self, state: dict[str, Any]) -> dict[str, Any] | tuple[dict[str, Any], str]:
        raise NotImplementedError

    def on_end(self, placement: list[int], reason: str) -> None:
        """Called once at game_end. Default impl is a no-op."""
