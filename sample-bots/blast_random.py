"""Uniform-random over legal actions — Blast leaderboard floor."""

from __future__ import annotations

import random

from vibewarz import Bot
from vibewarz_games.blast.game import Blast


class BlastRandomBot(Bot):
    game = "blast"
    display_name = "BlastRandomBot"

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self._engine = Blast()

    def act(self, state):
        legal = self._engine.legal_actions(state, self.seat)
        if not legal:
            return {"move": "stay", "drop_bomb": False}
        return self._rng.choice(legal)
