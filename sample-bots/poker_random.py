"""Uniform-random over legal actions. Useful as a stylistic foil and as a
chaos baseline for the leaderboard.
"""

from __future__ import annotations

import random

from vibewarz import Bot
from vibewarz_games.poker.betting import legal_actions


class PokerRandomBot(Bot):
    game = "poker"
    display_name = "PokerRandomBot"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def act(self, state):
        legal = legal_actions(state, self.seat)
        if not legal:
            return {"type": "check"}  # shouldn't be reached if we got asked
        return self._rng.choice(legal)
