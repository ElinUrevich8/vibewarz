"""Pure board generation + tile helpers for Blast.

Boards are `list[list[Cell]]` indexed `board[y][x]`. Cells are one of
``"empty" | "hard" | "soft"``. Hard walls are indestructible; soft blocks
are destroyed by flames.

The grid layout follows the classic SNES Super Blast pattern:
* outer border is all hard wall,
* every cell at (even x, even y) inside the border is a hard pillar,
* every other interior cell is filled with a soft block at ~70%
  probability, except an L-shaped safe pocket around each player's
  spawn so nobody starts trapped.

`generate_board` is deterministic in `(seed, num_players)`.
"""

from __future__ import annotations

import random
from typing import Final

BOARD_W: Final = 13
BOARD_H: Final = 11

SOFT_BLOCK_DENSITY: Final = 0.70

# Four corner spawns; the slice is taken according to num_players so a
# 2-player match uses opposite corners (max distance), 3-player adds the
# top-right corner, and 4-player fills all corners.
SPAWNS: Final = (
    (1, 1),                  # top-left
    (BOARD_W - 2, BOARD_H - 2),  # bottom-right (paired with top-left for 2p)
    (BOARD_W - 2, 1),        # top-right
    (1, BOARD_H - 2),        # bottom-left
)


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < BOARD_W and 0 <= y < BOARD_H


def _spawn_safe_tiles(spawns: list[tuple[int, int]]) -> set[tuple[int, int]]:
    """The spawn tile itself plus the two cardinal neighbours that aren't
    hard pillars — guarantees the player has at least one direction to
    escape on tick 0 without first destroying a block."""
    safe: set[tuple[int, int]] = set()
    for sx, sy in spawns:
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = sx + dx, sy + dy
            if in_bounds(nx, ny):
                safe.add((nx, ny))
    return safe


def generate_board(
    seed: int, num_players: int
) -> tuple[list[list[str]], list[tuple[int, int]]]:
    """Return ``(board, spawns)`` where ``spawns[i]`` is seat ``i``'s starting tile."""
    rng = random.Random(seed * 1_000_003 + 7)
    w, h = BOARD_W, BOARD_H
    board: list[list[str]] = [["empty"] * w for _ in range(h)]

    # Outer border: indestructible.
    for x in range(w):
        board[0][x] = "hard"
        board[h - 1][x] = "hard"
    for y in range(h):
        board[y][0] = "hard"
        board[y][w - 1] = "hard"

    # Inner pillars at even/even coordinates.
    for y in range(2, h - 1, 2):
        for x in range(2, w - 1, 2):
            board[y][x] = "hard"

    spawns = list(SPAWNS[:num_players])
    safe = _spawn_safe_tiles(spawns)

    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if board[y][x] != "empty":
                continue
            if (x, y) in safe:
                continue
            if rng.random() < SOFT_BLOCK_DENSITY:
                board[y][x] = "soft"

    return board, spawns
