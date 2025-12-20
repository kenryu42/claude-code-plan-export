# Agent Guidelines

## Commands
- **Setup**: `just setup` or `uv sync && uv run pre-commit install`
- **All checks**: `just check` (runs ruff, mypy, vulture, pytest)
- **Lint**: `uv run ruff check` | **Format**: `uv run ruff format`
- **Type check**: `uv run mypy .`
- **Test all**: `uv run pytest` | **Single test**: `uv run pytest tests/test_file.py::test_name -v`

## Code Style (Python 3.10+)
- **Formatter**: Ruff (88 char line length, 4-space indent)
- **Imports**: stdlib → third-party → local (sorted by isort via ruff)
- **Types**: All functions require type hints (`disallow_untyped_defs = true`)
- **Naming**: snake_case for functions/variables, use `Path` not string paths
- **Docstrings**: Module-level required, function docstrings for non-trivial logic
- **Error handling**: Print to stderr, return int exit codes (0=success, 1=error)
- **Union types**: Use `X | None` syntax (Python 3.10+), not `Optional[X]`

## Pre-commit Hooks
Runs automatically: ruff format → ruff check --fix → mypy → vulture (dead code)