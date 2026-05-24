"""Hand strength wrapper.

Only the evaluator from `pokerkit` is used. The betting state machine is ours
(see `betting.py` / `game.py`) because vibewarz's `Game` ABC requires pure
functions over JSON-serializable dicts, which pokerkit's stateful table
classes don't round-trip cleanly.

If we ever swap evaluators (e.g. to `treys`), this file is the only thing
that needs to change.
"""

from __future__ import annotations

from pokerkit import StandardHighHand
from pokerkit.lookups import Label

__all__ = ["Label", "best_seats", "label", "rank"]


def rank(hole: list[str], board: list[str]) -> StandardHighHand:
    """Best 5-card hand from 2 hole cards + 3-5 community cards.

    Returns a `StandardHighHand` that supports `<` / `==` for comparison.
    Requires len(hole)+len(board) >= 5, which our engine guarantees by
    running the board out to the river before any showdown.
    """
    return StandardHighHand.from_game("".join(hole), "".join(board))


def label(hand: StandardHighHand) -> Label:
    """Hand category as a typed enum (HIGH_CARD … STRAIGHT_FLUSH). Prefer
    this over `str(hand).startswith(...)` for hand-class decisions — the
    string format is not part of pokerkit's public API.
    """
    return hand.entry.label


def best_seats(seat_hands: dict[int, StandardHighHand]) -> list[int]:
    """Return the seats whose hand ties for best (split-pot candidates).

    Lower-ranked hands come first when sorted; pokerkit follows the convention
    that better hands compare *greater*. Ties are resolved by `==`.
    """
    if not seat_hands:
        return []
    best = max(seat_hands.values())
    return sorted(seat for seat, h in seat_hands.items() if h == best)
