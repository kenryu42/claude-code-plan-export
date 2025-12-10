# Claude Code Plan Export

Auto-save your Claude Code plans to the project root when you finish planning.

## Features

- **Automatic Export** - Plans are exported when your Claude Code session ends
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

## Usage

### Automatic Export (Default)

When you exit a Claude Code session that used plan mode, the plugin automatically copies your plan file from `~/.claude/plans/` to your project root as `plan-{slug}.md`.

### Manual Export

Export all plans from the current project:

```
/export-project-plans
```

This scans all session transcripts and exports any associated plan files.

## How It Works

1. **SessionStart** - Captures the transcript path for later use
2. **SessionEnd** - Reads the transcript, finds the plan `slug`, copies `~/.claude/plans/{slug}.md` to `plan-{slug}.md`

## Project Structure

```
.claude-plugin/
  plugin.json           # Plugin metadata
hooks/
  hooks.json            # Hook definitions
scripts/
  session_start.py      # SessionStart hook
  export_plan.py        # SessionEnd hook
  export_project_plans.py  # Manual export command
commands/
  export-project-plans.md  # Slash command definition
```

## Development

Run tests:

```bash
python3 tests/run_tests.py
```

## License

MIT
