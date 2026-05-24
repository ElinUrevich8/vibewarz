.PHONY: install test lint typecheck play-local-demo build

install:
	uv sync --all-extras

test:
	uv run --extra dev pytest

lint:
	uvx ruff check .

typecheck:
	uvx mypy games/src sdk-python/src

play-local-demo:
	uv run --package vibewarz vibewarz play-local --game curve \
		--bot sample-bots/curve_wall_avoid.py \
		--bot sample-bots/curve_wall_avoid.py \
		--bot sample-bots/curve_wall_avoid.py \
		--bot sample-bots/curve_wall_avoid.py

build:
	cd games && uv build
	cd sdk-python && uv build
