# Install dependencies
setup:
    uv sync
    uv run pre-commit install

# Run linter, type checker, dead code detection, and tests
check:
    # Run linter
    uv run ruff check
    # Run type checker
    uv run mypy .
    # Run dead code detection
    uv run vulture
    # Run tests
    uv run pytest
