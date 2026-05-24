"""Flame propagation tests for Blast."""

from __future__ import annotations

from vibewarz_games.blast.board import BOARD_H, BOARD_W, generate_board
from vibewarz_games.blast.bombs import explosion_tiles


def _empty_board() -> list[list[str]]:
    """All-empty interior; only the outer border is hard."""
    board = [["empty"] * BOARD_W for _ in range(BOARD_H)]
    for x in range(BOARD_W):
        board[0][x] = "hard"
        board[BOARD_H - 1][x] = "hard"
    for y in range(BOARD_H):
        board[y][0] = "hard"
        board[y][BOARD_W - 1] = "hard"
    return board


def test_origin_always_in_flame() -> None:
    board = _empty_board()
    flame, destroyed = explosion_tiles(board, 5, 5, blast_range=0)
    assert flame == {(5, 5)}
    assert destroyed == set()


def test_range_extends_in_four_directions() -> None:
    board = _empty_board()
    flame, _ = explosion_tiles(board, 5, 5, blast_range=2)
    assert (5, 5) in flame
    for d in (1, 2):
        assert (5 + d, 5) in flame
        assert (5 - d, 5) in flame
        assert (5, 5 + d) in flame
        assert (5, 5 - d) in flame
    # Range 2 only — tile at offset 3 is NOT lit.
    assert (5 + 3, 5) not in flame


def test_hard_wall_blocks_ray_and_is_not_lit() -> None:
    board = _empty_board()
    # Border at column 12 is hard. Bomb at (10,5) with range 5 should reach
    # (11,5) but stop at (12,5) — and (12,5) must NOT be in the flame set.
    flame, _ = explosion_tiles(board, 10, 5, blast_range=5)
    assert (11, 5) in flame
    assert (12, 5) not in flame
    assert (13, 5) not in flame


def test_soft_block_burns_then_stops_ray() -> None:
    board = _empty_board()
    board[5][7] = "soft"
    flame, destroyed = explosion_tiles(board, 5, 5, blast_range=5)
    # ray east lights (6,5) and (7,5), then stops — (8,5) is shielded.
    assert (6, 5) in flame
    assert (7, 5) in flame
    assert (8, 5) not in flame
    assert (7, 5) in destroyed


def test_real_board_respects_inner_pillars() -> None:
    board, _ = generate_board(seed=1, num_players=4)
    # The pillar at (2, 2) blocks the east ray from (1, 2).
    # (1, 2) is in the spawn-safe pocket of seat 0 so it's empty.
    flame, _ = explosion_tiles(board, 1, 2, blast_range=5)
    assert (2, 2) not in flame
