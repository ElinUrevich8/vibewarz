# vibewarz

Open-source bot-vs-bot arena. Write a Python bot, climb the ELO leaderboard at [vibewarz.com](https://vibewarz.com).

This repo contains the public surface:

| Package | What |
|---|---|
| [`sdk-python/`](sdk-python/) | `vibewarz` — Bot base class, WebSocket client, protocol models, `play-local` harness |
| [`games/`](games/) | `vibewarz-games` — pure Python game engines (Curve, Poker, Blast) |
| [`sample-bots/`](sample-bots/) | Reference bots you can fork |
| [`docs/`](docs/) | Protocol spec + quickstart + game-authoring guide |

The closed-source platform (server, web UI, infra) lives at [OmriGanor/vibe-warz-platform](https://github.com/OmriGanor/vibe-warz-platform).

## Quickstart

```bash
pip install vibewarz vibewarz-games

# Run a 4-bot Curve match locally — no server, no auth:
vibewarz play-local --game curve \
  --bot sample-bots/curve_wall_avoid.py \
  --bot sample-bots/curve_wall_avoid.py \
  --bot sample-bots/curve_wall_avoid.py \
  --bot sample-bots/curve_wall_avoid.py

# Or 2-bot heads-up poker:
vibewarz play-local --game poker \
  --bot sample-bots/poker_random.py \
  --bot sample-bots/poker_random.py
```

Write your own:

```python
# my_bot.py
from vibewarz import Bot

class MyBot(Bot):
    game = "curve"
    def act(self, state):
        return {"turn": "STRAIGHT"}
```

```bash
# 4 players minimum for curve; mix yours with samples:
vibewarz play-local --game curve \
  --bot my_bot.py \
  --bot sample-bots/curve_wall_avoid.py \
  --bot sample-bots/curve_wall_avoid.py \
  --bot sample-bots/curve_wall_avoid.py
```

Ready to climb the ladder? Get an API key at [vibewarz.com](https://vibewarz.com), then:

```bash
export VIBEWARZ_API_KEY=sk_live_...
vibewarz play my_bot.py --mode ranked --loop 50
```

See [`docs/QUICKSTART.md`](docs/QUICKSTART.md) for the full walkthrough and [`docs/PROTOCOL.md`](docs/PROTOCOL.md) for the wire spec.

## Develop on this repo

```bash
uv sync --all-extras
make test     # pytest games + sdk
make lint     # ruff
```

## License

MIT — see [LICENSE](LICENSE).
