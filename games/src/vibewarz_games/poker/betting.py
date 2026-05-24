"""Pure helpers for the NLH betting state machine.

State is a JSON-serializable dict shared with `game.py`. Every function in
this module is a pure (state, ...) -> new_state transformation. No I/O.
"""

from __future__ import annotations

import random
from typing import Any, Final

RANKS: Final = "23456789TJQKA"
SUITS: Final = "shdc"
FULL_DECK: Final = tuple(r + s for r in RANKS for s in SUITS)

# Visual palette mirrored on the frontend.
PLAYER_COLORS: Final = (
    "#a3e635",  # lime
    "#f43f5e",  # red
    "#38bdf8",  # sky
    "#fbbf24",  # amber
    "#c084fc",  # purple
    "#22d3ee",  # cyan
)


def new_shuffled_deck(seed: int, hand_number: int) -> list[str]:
    """Deterministic per-hand deck. Same (seed, hand_number) → same deck."""
    rng = random.Random(seed * 1_000_003 + hand_number * 9_999_999)
    deck = list(FULL_DECK)
    rng.shuffle(deck)
    return deck


# ── seat traversal ─────────────────────────────────────────────────────────


def in_tournament_seats(state: dict) -> list[int]:
    return sorted(p["seat"] for p in state["players"] if p["in_tournament"])


def in_hand_seats(state: dict) -> list[int]:
    return sorted(p["seat"] for p in state["players"] if p["in_hand"])


def eligible_to_act(state: dict) -> list[int]:
    """Seats that still owe a decision in the current betting round
    (in_hand AND not all_in)."""
    return sorted(
        p["seat"]
        for p in state["players"]
        if p["in_hand"] and not p["all_in"]
    )


def _seat(state: dict, seat: int) -> dict:
    for p in state["players"]:
        if p["seat"] == seat:
            return p
    raise KeyError(f"seat {seat} not found")


def next_clockwise(state: dict, start_seat: int, predicate) -> int | None:
    """Walk clockwise from start_seat+1 around all seats in seat-id order
    (treated as circular), returning the first seat that satisfies the
    predicate. Returns None if none match. The start seat itself is skipped.
    """
    n = len(state["players"])
    for i in range(1, n + 1):
        candidate = (start_seat + i) % n
        if predicate(_seat(state, candidate)):
            return candidate
    return None


# ── betting round bookkeeping ──────────────────────────────────────────────


def is_round_complete(state: dict) -> bool:
    """Betting round is complete when every in_hand seat has either matched
    `current_bet` or is all-in, and every still-eligible seat has acted at
    least once since the last aggression."""
    eligible = [p for p in state["players"] if p["in_hand"] and not p["all_in"]]
    if not eligible:
        return True
    current_bet = state["current_bet"]
    acted = set(state.get("acted_this_round") or [])
    return all(p["committed_round"] == current_bet and p["seat"] in acted for p in eligible)


def next_to_act(state: dict, after_seat: int | None) -> int | None:
    """First seat clockwise from `after_seat` that still owes action this
    round, or None if the round is complete. `after_seat=None` means start
    from seat -1 (i.e. include seat 0 if eligible).
    """
    current_bet = state["current_bet"]
    acted = set(state.get("acted_this_round") or [])

    def owes(p: dict) -> bool:
        return (
            p["in_hand"]
            and not p["all_in"]
            and (p["committed_round"] < current_bet or p["seat"] not in acted)
        )

    start = after_seat if after_seat is not None else len(state["players"]) - 1
    return next_clockwise(state, start, owes)


# ── action application ─────────────────────────────────────────────────────


def legal_actions(state: dict, seat: int) -> list[dict]:
    p = _seat(state, seat)
    if not p["in_hand"] or p["all_in"]:
        return []
    to_call = state["current_bet"] - p["committed_round"]
    actions: list[dict] = [{"type": "fold"}]
    if to_call <= 0:
        actions.append({"type": "check"})
    else:
        actions.append({"type": "call"})  # may be a partial all-in call

    stack = p["stack"]
    committed = p["committed_round"]
    # Opening bet (no current bet) — amount in [bb, stack].
    if state["current_bet"] == 0:
        min_open = max(state.get("big_blind", 1), 1)
        if stack >= min_open:
            actions.append({"type": "bet", "amount": min_open})
            if stack > min_open:
                actions.append({"type": "bet", "amount": stack})  # all-in
        elif stack > 0:
            actions.append({"type": "bet", "amount": stack})
    else:
        # Raise. NLH no-reopen rule: when the most recent aggression was an
        # under-min-raise all-in, seats that had already acted at the prior
        # bet level can no longer raise — only call or fold. Fresh-to-the-
        # round seats still get full options.
        locked = seat in (state.get("raise_locked_seats") or [])
        if not locked:
            full_min = state["current_bet"] + state["min_raise"]
            max_total = stack + committed
            if max_total > state["current_bet"]:
                if max_total >= full_min:
                    actions.append({"type": "raise", "to": full_min})
                    if max_total > full_min:
                        actions.append({"type": "raise", "to": max_total})  # all-in
                else:
                    # Short stack all-in for less than a full raise — still legal.
                    actions.append({"type": "raise", "to": max_total})
    return actions


def is_legal(state: dict, seat: int, action: Any) -> bool:
    if not isinstance(action, dict):
        return False
    typ = action.get("type")
    p = _seat(state, seat)
    if not p["in_hand"] or p["all_in"]:
        return False
    if typ == "fold":
        return True
    to_call = state["current_bet"] - p["committed_round"]
    if typ == "check":
        return to_call <= 0
    if typ == "call":
        return to_call > 0
    if typ == "bet":
        if state["current_bet"] != 0:
            return False
        amount = action.get("amount")
        if not isinstance(amount, int) or amount <= 0:
            return False
        if amount > p["stack"]:
            return False
        bb = state.get("big_blind", 1)
        return amount >= bb or amount == p["stack"]
    if typ == "raise":
        if state["current_bet"] == 0:
            return False
        if seat in (state.get("raise_locked_seats") or []):
            # No-reopen: this seat already acted at the prior bet level and
            # the most recent aggression was an under-min-raise all-in.
            return False
        to = action.get("to")
        if not isinstance(to, int):
            return False
        max_total = p["stack"] + p["committed_round"]
        if to <= state["current_bet"] or to > max_total:
            return False
        full_min = state["current_bet"] + state["min_raise"]
        return to >= full_min or to == max_total  # short-stack all-in raise
    return False


def apply_action(state: dict, seat: int, action: dict) -> dict:
    """Apply one legal action by `seat`. Returns new state; does not advance
    actor or phase (caller does that)."""
    typ = action["type"]
    players = [dict(p) for p in state["players"]]
    p = next(pl for pl in players if pl["seat"] == seat)
    history = list(state.get("history") or [])
    acted = list(state.get("acted_this_round") or [])
    raise_locked = list(state.get("raise_locked_seats") or [])
    current_bet = state["current_bet"]
    min_raise = state["min_raise"]
    last_aggressor = state.get("last_aggressor")

    if typ == "fold":
        p["in_hand"] = False
        p["folded"] = True
    elif typ == "check":
        pass
    elif typ == "call":
        owe = current_bet - p["committed_round"]
        pay = min(owe, p["stack"])
        p["stack"] -= pay
        p["committed_round"] += pay
        p["committed_hand"] += pay
        if p["stack"] == 0:
            p["all_in"] = True
    elif typ == "bet":
        amount = int(action["amount"])
        full_min = max(state.get("big_blind", 1), 1)
        p["stack"] -= amount
        p["committed_round"] += amount
        p["committed_hand"] += amount
        if p["stack"] == 0:
            p["all_in"] = True
        current_bet = p["committed_round"]
        last_aggressor = seat
        if amount >= full_min:
            min_raise = amount
            acted = []
            raise_locked = []
        else:
            # Short-stack open-bet below the BB. Engine permits it (must be
            # all-in). Doesn't satisfy min-raise → seats that get a fresh
            # decision because current_bet went up may NOT raise (no-reopen).
            previously_acted = [s for s in acted if s != seat]
            raise_locked = sorted(set(raise_locked + previously_acted))
            acted = []  # everyone still owes a decision at the new bet
    elif typ == "raise":
        to = int(action["to"])
        increment = to - p["committed_round"]
        p["stack"] -= increment
        p["committed_round"] = to
        p["committed_hand"] += increment
        if p["stack"] == 0:
            p["all_in"] = True
        raise_size = to - current_bet
        if raise_size >= min_raise:
            min_raise = raise_size
            acted = []
            raise_locked = []  # full raise resets the no-reopen tracker
        else:
            # Under-min-raise all-in: by NLH rule, seats that already acted
            # at the prior bet level cannot re-raise — only call/fold. They
            # are not in `acted` for the new bet (current_bet went up), so
            # they DO owe action; we track the restriction separately.
            previously_acted = [s for s in acted if s != seat]
            raise_locked = sorted(set(raise_locked + previously_acted))
            acted = [s for s in acted if s == seat]
        current_bet = to
        last_aggressor = seat

    p["last_action"] = action
    if seat not in acted:
        acted.append(seat)
    history.append({
        "hand": state["hand_number"],
        "phase": state["phase"],
        "seat": seat,
        "action": action,
    })

    return {
        **state,
        "players": players,
        "current_bet": current_bet,
        "min_raise": min_raise,
        "last_aggressor": last_aggressor,
        "acted_this_round": acted,
        "raise_locked_seats": raise_locked,
        "history": history,
    }


# ── phase transitions ──────────────────────────────────────────────────────


PHASE_ORDER: Final = ("preflop", "flop", "turn", "river", "showdown")
DEAL_PER_PHASE: Final = {"flop": 3, "turn": 1, "river": 1, "showdown": 0}


def commit_round_to_pot(state: dict) -> dict:
    """Move committed_round chips into the central pot and reset for next round."""
    pot = state["pot"] + sum(p["committed_round"] for p in state["players"])
    players = [{**p, "committed_round": 0} for p in state["players"]]
    return {**state, "pot": pot, "players": players, "current_bet": 0,
            "min_raise": state.get("big_blind", 1), "acted_this_round": [],
            "raise_locked_seats": [], "last_aggressor": None}


def deal_community(state: dict, n: int) -> dict:
    """Deal N community cards, discarding one card before each dealt card.

    Note this discards N cards in total (one per dealt card), which is
    slightly different from real-poker convention (one burn per street, not
    one per card — so 3 burns for a flop+turn+river instead of 5). The
    discards are never observable: the deck is redacted in `view_for` and
    the burned cards are never used. The pattern is kept purely so the
    deck order remains a stable function of (seed, hand_number).
    """
    deck = list(state["deck"])
    cards = list(state["community_cards"])
    for _ in range(n):
        if deck:
            deck.pop(0)  # discard
        if deck:
            cards.append(deck.pop(0))
    return {**state, "deck": deck, "community_cards": cards}


def advance_phase(state: dict) -> dict:
    """Move from current phase to the next. Caller is responsible for first
    committing the round (`commit_round_to_pot`)."""
    cur = state["phase"]
    idx = PHASE_ORDER.index(cur)
    nxt = PHASE_ORDER[idx + 1]
    state = {**state, "phase": nxt}
    if nxt in DEAL_PER_PHASE and DEAL_PER_PHASE[nxt] > 0:
        state = deal_community(state, DEAL_PER_PHASE[nxt])
    return state


def first_to_act_postflop(state: dict) -> int | None:
    """First in_hand & not all_in seat clockwise from the button."""
    button = state["button"]
    return next_clockwise(
        state, button,
        lambda p: p["in_hand"] and not p["all_in"],
    )


# ── side pots ──────────────────────────────────────────────────────────────


def build_pots(state: dict) -> list[dict]:
    """Given finalized per-hand commitments, partition into main + side pots.
    Each pot: {"amount": int, "eligible_seats": list[int]}.

    Eligible = in_hand seats whose committed_hand >= layer threshold.
    """
    commits = {p["seat"]: p["committed_hand"] for p in state["players"] if p["committed_hand"] > 0}
    in_hand = {p["seat"] for p in state["players"] if p["in_hand"]}
    if not commits:
        return []
    layers = sorted(set(commits.values()))
    pots: list[dict] = []
    prev = 0
    for layer in layers:
        layer_size = layer - prev
        contributors = [s for s, c in commits.items() if c >= layer]
        amount = layer_size * len(contributors)
        eligible = sorted(s for s in contributors if s in in_hand)
        if amount > 0:
            if pots and pots[-1]["eligible_seats"] == eligible:
                pots[-1]["amount"] += amount
            else:
                pots.append({"amount": amount, "eligible_seats": eligible})
        prev = layer
    return pots
