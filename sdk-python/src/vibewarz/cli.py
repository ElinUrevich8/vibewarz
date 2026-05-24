"""CLI: `vibewarz login`, `vibewarz play <script>`, `vibewarz replay <id>`,
`vibewarz play-local --game <id> --bot a.py --bot b.py`."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import httpx
import typer

from .bot import Bot
from .client import default_api_url
from .play_local import play as play_in_process
from .runner import run as run_bot

app = typer.Typer(add_completion=False, help="vibewarz — write bots, climb leaderboards.")


def _api_http_url() -> str:
    ws = default_api_url()
    if ws.startswith("ws://"):
        return "http://" + ws[5:].rstrip("/").removesuffix("/ws")
    if ws.startswith("wss://"):
        return "https://" + ws[6:].rstrip("/").removesuffix("/ws")
    return ws


def _credentials_path() -> Path:
    return Path.home() / ".vibewarz" / "credentials"


@app.command()
def login(display_name: str = typer.Option(None, help="Optional display name for guest mode.")) -> None:
    """Mint a guest token and store it (placeholder — GitHub OAuth lands later)."""
    base = _api_http_url()
    r = httpx.post(f"{base}/auth/guest", params={"display_name": display_name} if display_name else None)
    r.raise_for_status()
    data = r.json()
    creds_path = _credentials_path()
    creds_path.parent.mkdir(parents=True, exist_ok=True)
    creds_path.write_text(json.dumps(data, indent=2))
    typer.echo(f"Logged in as {data['user']['handle']} (guest). Token stored in {creds_path}.")


@app.command()
def play(
    script: Path = typer.Argument(..., exists=True, readable=True, help="Path to a .py file containing a Bot subclass."),
    mode: str = typer.Option("practice", help="ranked | practice | challenge"),
    loop: int = typer.Option(1, help="Number of matches to play in a row."),
    bot_label: str = typer.Option(None, help="Label shown in replays."),
    guest_name: str = typer.Option(None, help="Override guest display name."),
) -> None:
    """Run a bot script against the live API."""
    spec = importlib.util.spec_from_file_location("user_bot_module", script)
    if spec is None or spec.loader is None:
        typer.echo(f"Could not load {script}", err=True)
        raise typer.Exit(1)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["user_bot_module"] = mod
    spec.loader.exec_module(mod)

    bot_cls = None
    for name in dir(mod):
        obj = getattr(mod, name)
        if isinstance(obj, type) and issubclass(obj, Bot) and obj is not Bot:
            bot_cls = obj
            break
    if bot_cls is None:
        typer.echo("No Bot subclass found in script.", err=True)
        raise typer.Exit(1)

    run_bot(bot_cls(), mode=mode, loop=loop, bot_label=bot_label, guest_name=guest_name)


@app.command("play-local")
def play_local(
    game: str = typer.Option(..., help="Game id, e.g. curve | poker | blast."),
    bot: list[Path] = typer.Option(..., "--bot", help="Path to a bot script. Pass --bot once per seat."),
    seed: int = typer.Option(None, help="Random seed for reproducible matches."),
    max_ticks: int = typer.Option(None, help="Override the game's default max-ticks limit."),
    verbose: bool = typer.Option(False, help="Print eliminations + illegal-action substitutions."),
) -> None:
    """Run an in-process match between N bot scripts. No server, no auth."""
    for p in bot:
        if not p.exists() or not p.is_file():
            typer.echo(f"bot file not found: {p}", err=True)
            raise typer.Exit(1)
    try:
        result = play_in_process(
            game_id=game,
            bot_paths=list(bot),
            seed=seed,
            max_ticks=max_ticks,
            verbose=verbose,
        )
    except RuntimeError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(1) from e
    typer.echo(
        f"{result.match_id}: placement={result.placement} reason={result.reason} ticks={result.ticks}"
    )


@app.command()
def replay(match_id: str) -> None:
    """Print a replay's tick log to stdout (pretty)."""
    # Naively walk ./data/replays for the file — useful when running locally.
    root = Path("./data/replays").resolve()
    candidates = list(root.rglob(f"{match_id}.jsonl"))
    if not candidates:
        typer.echo(f"No replay file found for {match_id} under {root}", err=True)
        raise typer.Exit(1)
    for line in candidates[0].read_text().splitlines():
        obj = json.loads(line)
        typer.echo(json.dumps(obj, indent=2))


if __name__ == "__main__":
    app()
