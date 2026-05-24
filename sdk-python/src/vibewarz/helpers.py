"""Bot-side helpers for common per-game state plumbing.

These are optional — bots can ignore them and parse `state` directly.
"""

from __future__ import annotations

from typing import Any


class TrailTracker:
    """Reconstructs full per-seat trails from `game_start` + `tick_request` deltas.

    The server sends full `trails` only once at `game_start`; subsequent ticks
    carry just `trail_delta`. Most non-trivial Curve bots need the full trail
    field for collision reasoning, so this helper centralizes the merge.

    Usage:

        class MyBot(Bot):
            game = "curve"
            def __init__(self):
                self.trails = TrailTracker()
            def on_start(self, initial_state):
                self.trails.on_start(initial_state)
            def act(self, state):
                self.trails.update(state)
                full = self.trails.trails  # list[list[(x, y)]]
                ...
    """

    def __init__(self) -> None:
        self.trails: list[list[tuple[float, float]]] = []

    def on_start(self, initial_state: dict[str, Any]) -> None:
        self.trails = [list(t) for t in initial_state.get("trails", [])]

    def update(self, state: dict[str, Any]) -> list[list[tuple[float, float]]]:
        """Append the latest `trail_delta` onto each per-seat trail.

        Falls back to seeding from `state["trails"]` if `on_start` was skipped
        (e.g. bot reconnect mid-match).
        """

        if not self.trails:
            self.trails = [list(t) for t in state.get("trails", [])]
        delta = state.get("trail_delta") or []
        for seat, new_points in enumerate(delta):
            if seat < len(self.trails):
                self.trails[seat].extend(new_points)
        return self.trails
