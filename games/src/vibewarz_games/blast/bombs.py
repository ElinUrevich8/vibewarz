"""Pure flame-propagation helpers.

Splitting this from ``game.py`` keeps the explosion rules unit-testable
without spinning up a whole match, and lets the frontend "danger preview"
or a bot's lookahead use the exact same code the authoritative engine
uses.
"""

from __future__ import annotations

from .board import BOARD_H, BOARD_W


def explosion_tiles(
    board: list[list[str]], x: int, y: int, blast_range: int
) -> tuple[set[tuple[int, int]], set[tuple[int, int]]]:
    """Return ``(flame_tiles, destroyed_soft)`` for a bomb at ``(x, y)``.

    The bomb's own tile is always in ``flame_tiles``. Each cardinal ray
    walks outward up to ``blast_range`` cells, stopping immediately at a
    hard wall (which does NOT catch fire) and stopping just after a soft
    block (which catches fire AND is destroyed — only the first soft
    block in each ray, classic shielding rules).
    """
    flame: set[tuple[int, int]] = {(x, y)}
    destroyed_soft: set[tuple[int, int]] = set()
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for i in range(1, blast_range + 1):
            nx, ny = x + dx * i, y + dy * i
            if not (0 <= nx < BOARD_W and 0 <= ny < BOARD_H):
                break
            cell = board[ny][nx]
            if cell == "hard":
                break
            flame.add((nx, ny))
            if cell == "soft":
                destroyed_soft.add((nx, ny))
                break
    return flame, destroyed_soft
