# Writing a new game for vibewarz

A new vibewarz game is two things:

1. A pure-Python `Game` subclass in [`games/src/vibewarz_games/<slug>/game.py`](../games/src/vibewarz_games/) — the authoritative rules engine.
2. (For the live arena only) a TypeScript renderer in the closed [vibe-warz-platform](https://github.com/OmriGanor/vibe-warz-platform) repo. Local play doesn't need this.

This guide covers (1). If you'd like a renderer in the live arena, open an issue here and we'll coordinate.

## The `Game` interface

```python
from vibewarz_games._core.base import Game, GameMeta, StepResult
from vibewarz_games._core.registry import register


@register
class MyGame(Game):
    meta = GameMeta(
        id="my-game",
        display_name="My Game",
        min_players=2,
        max_players=4,
        tick_deadline_ms=50,
        max_ticks=1000,
    )

    def initial_state(self, seed: int, num_players: int) -> dict:
        return {"tick": 0, "scores": [0] * num_players, "rng_seed": seed}

    def alive_seats(self, state: dict) -> list[int]:
        return [s for s, score in enumerate(state["scores"]) if score < 10]

    def legal_actions(self, state: dict, seat: int) -> list[dict]:
        return [{"play": "a"}, {"play": "b"}]

    def is_legal(self, state: dict, seat: int, action: dict) -> bool:
        return action.get("play") in ("a", "b")

    def default_action(self, state: dict, seat: int) -> dict:
        return {"play": "a"}

    def step(self, state: dict, actions: dict[int, dict]) -> StepResult:
        new_scores = list(state["scores"])
        for seat, action in actions.items():
            if action["play"] == "a":
                new_scores[seat] += 1
        new_state = {**state, "tick": state["tick"] + 1, "scores": new_scores}
        winners = [s for s, sc in enumerate(new_scores) if sc >= 10]
        if winners:
            placement = sorted(range(len(new_scores)), key=lambda s: -new_scores[s])
            return StepResult(state=new_state, done=True, placement=placement, reason="score_reached")
        return StepResult(state=new_state)
```

## Rules

- **Pure**: no I/O, no mutation of inputs, no module-level globals that store state. All randomness flows from `seed`.
- **Deterministic**: `(state, actions)` → exactly one `StepResult`. Same inputs, same outputs, every time. Replays depend on this.
- **JSON-safe state**: state must round-trip through `json.dumps`/`json.loads`. Only dict, list, str, int, float, bool, None.
- **Per-seat views via `view_for`**: if your game has hidden information (cards, fog of war), override `view_for(state, seat)` to redact the public view. The unredacted state stays on the server.
- **Turn-based games override `acting_seats`**: default is "every alive seat acts every tick" (simultaneous-move, like Curve). For poker we return only the seat on the clock.

## Wire up the registry

Import your game module from `games/src/vibewarz_games/__init__.py` so the `@register` decorator runs:

```python
# games/src/vibewarz_games/__init__.py
from . import blast, curve, my_game, poker  # noqa: F401
```

## Test it

Add tests under `games/tests/test_my_game.py`. Cover at minimum:

- `initial_state` returns the right shape for each player count in `[min_players, max_players]`
- A complete simulated match converges (no infinite loops)
- Each action in `legal_actions(state, seat)` returns `True` from `is_legal`
- `default_action` returns something `is_legal` accepts
- Replay determinism: two `step()` calls with the same inputs produce the same `StepResult`

Run with `make test`.

## Play it locally

```bash
# Write a stub bot in my_game_random.py:
cat > /tmp/my_game_random.py <<'EOF'
import random
from vibewarz import Bot
from vibewarz_games import GAMES

class RandomBot(Bot):
    game = "my-game"
    def __init__(self):
        self._eng = GAMES["my-game"]()
    def act(self, state):
        return random.choice(self._eng.legal_actions(state, self.seat))
EOF

vibewarz play-local --game my-game --bot /tmp/my_game_random.py --bot /tmp/my_game_random.py
```

## Get it on the live arena

Open a PR here with the game + tests. We'll review and, once merged + tagged, the closed platform repo pulls in the new `vibewarz-games` version and we'll add the renderer to ship it on [vibewarz.com](https://vibewarz.com).
