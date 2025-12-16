# Claude Code Plan Export

Auto-save your Claude Code plans to the project root when you finish planning in `Plan Mode`.

## Why Use This Plugin?

- **Optimize token usage** - Plan with Opus 4.5 for quality, then execute with faster, cheaper models
- **Clean implementation context** - Start each implementation with a fresh context window, avoiding artifacts from planning sessions
- **Flexible workflows** - Plan once, then execute with any model you choose, not just Claude Code
- **Zero Passive Context Cost** - Unlike plugins that rely on MCP servers or Skills, this plugin adds no overhead to the context window.

## Features

- **Automatic Export** - Plans are exported when your start a new session or exit Claude Code
- **Manual Export** - Use `/export-project-plans` to export all plans from the current project
- **Concurrent Session Support** - Handles multiple Claude Code sessions safely with file locking

## Installation

Add the marketplace to Claude Code:

```
/plugin marketplace add kenryu42/cc-marketplace
```

Install the plugin:

```
/plugin install plan-export@cc-marketplace
```

> [!NOTE]
> You'll need to restart Claude Code in order to use the new plugin.

## Auto-Update

1. Run `/plugin` to open the plugin manager
2. Select `Marketplaces`
3. Choose `cc-marketplace` from the list
4. Select `Enable auto-update`

## Usage

### Automatic Export (Default)

When you exit a Claude Code session that used plan mode, the plugin automatically copies your plan file from `~/.claude/plans/` to your project root as `plan-{slug}.md`.

### Manual Export

Export all plans from the current project:

```
/export-project-plans
```

This scans all session transcripts and exports any associated plan files.

Export all plans with timestamps:

```
/export-project-plans-with-timestamp
```

This exports plans with the source file's last modified time prepended: `YYYYMMDD-HHMMSS-plan-{slug}.md`

### Execute Plan

Execute the most recent plan in the current directory:

```
/execute-plan
```

This finds the most recently modified `*plan-*.md` file and executes it.

## How It Works

1. Plan with Opus or any model in Plan Mode as usual
2. When it asks you to choose auto-accept or manual approval, press **Esc**
3. Start a new session (`/clear`, `/reset`, or `/new`)
4. Your plan is automatically exported to your current working directory as `plan-{original_uid}.md`

From there, you can execute the plan with whatever model you prefer.

## Project Structure

```
.claude-plugin/
  plugin.json
hooks/
  hooks.json
scripts/
  session_start.py
  export_plan.py
  export_project_plans.py
  export_project_plans_with_timestamp.py
commands/
  export-project-plans.md
  export-project-plans-with-timestamp.md
  execute-plan.md
```

## Development

```bash
# Option 1: Using just (Recommended)
# Install dependencies and setup hooks
just setup

# Run all checks (tests, lint, type check, dead code)
just check

# Option 2: Manual commands
# Install dependencies
uv sync

# Setup pre-commit hooks
uv run pre-commit install

# Run tests
uv run pytest

# Run linter
uv run ruff check

# Run type checker
uv run mypy .

# Run dead code detection
uv run vulture

```

## License

MIT
