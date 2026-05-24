"""Board-generation tests for Blast."""

from __future__ import annotations

from vibewarz_games.blast.board import (
    BOARD_H,
    BOARD_W,
    SPAWNS,
    generate_board,
    in_bounds,
)


def test_board_dimensions_and_border() -> None:
    board, _ = generate_board(seed=1, num_players=4)
    assert len(board) == BOARD_H
    assert all(len(row) == BOARD_W for row in board)
    for x in range(BOARD_W):
        assert board[0][x] == "hard"
        assert board[BOARD_H - 1][x] == "hard"
    for y in range(BOARD_H):
        assert board[y][0] == "hard"
        assert board[y][BOARD_W - 1] == "hard"


def test_inner_pillars_at_even_even() -> None:
    board, _ = generate_board(seed=1, num_players=4)
    for y in range(2, BOARD_H - 1, 2):
        for x in range(2, BOARD_W - 1, 2):
            assert board[y][x] == "hard", f"expected hard pillar at ({x},{y})"


def test_spawn_safe_tiles_are_clear() -> None:
    board, spawns = generate_board(seed=1, num_players=4)
    for sx, sy in spawns:
        assert board[sy][sx] == "empty"
        # at least one cardinal neighbour must be empty so the player can
        # walk off tick 0 without first destroying a block
        clears = 0
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = sx + dx, sy + dy
            if in_bounds(nx, ny) and board[ny][nx] == "empty":
                clears += 1
        assert clears >= 1


def test_seeded_determinism() -> None:
    a, sa = generate_board(seed=123, num_players=4)
    b, sb = generate_board(seed=123, num_players=4)
    c, _ = generate_board(seed=124, num_players=4)
    assert a == b
    assert sa == sb
    assert a != c


def test_two_player_uses_opposite_corners() -> None:
    _, spawns = generate_board(seed=1, num_players=2)
    assert spawns[0] == SPAWNS[0]
    assert spawns[1] == SPAWNS[1]
    # opposite diagonal — maximally separated
    (x0, y0), (x1, y1) = spawns
    assert abs(x0 - x1) == BOARD_W - 3
    assert abs(y0 - y1) == BOARD_H - 3


def test_soft_blocks_in_density_window() -> None:
    # Over many seeds, soft-block density on candidate tiles should hover
    # near 0.70. With ~80 candidate tiles per board this is a coarse band.
    totals = 0
    softs = 0
    for seed in range(20):
        board, _ = generate_board(seed=seed, num_players=4)
        for y in range(1, BOARD_H - 1):
            for x in range(1, BOARD_W - 1):
                if (x % 2 == 0) and (y % 2 == 0):
                    continue  # hard pillar
                totals += 1
                if board[y][x] == "soft":
                    softs += 1
    density = softs / totals
    assert 0.55 <= density <= 0.80
