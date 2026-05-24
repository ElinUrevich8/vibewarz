"""Game registry. Each game module decorates its class with @register and the
package's __init__ imports each game module so registration happens on import.
"""

from __future__ import annotations

from typing import TypeVar

from .base import Game

T = TypeVar("T", bound=type[Game])

GAMES: dict[str, type[Game]] = {}


def register(cls: T) -> T:
    GAMES[cls.meta.id] = cls
    return cls


def get(game_id: str) -> type[Game]:
    return GAMES[game_id]
