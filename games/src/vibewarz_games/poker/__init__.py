"""No-Limit Texas Hold'em — single-table tournament.

Importing this module registers `Poker` in the global `GAMES` dict.
"""

from . import game as _game  # noqa: F401  side-effect: registers Poker
