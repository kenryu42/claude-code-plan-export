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

Export all plans with timestamps:

```
/export-project-plans-with-timestamp
```

This exports plans with the source file's last modified time prepended: `YYYYMMDD-HH:MM:SS-plan-{slug}.md`

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
  export_project_plans_with_timestamp.py  # Manual export command with timestamp prefix
commands/
  export-project-plans.md  # Slash command definition
  export-project-plans-with-timestamp.md  # Slash command definition
  execute-plan.md          # Execute most recent plan
```

## Development

Run tests:

```bash
python3 tests/run_tests.py
```

## License

MIT
