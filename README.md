# Claude Code Plan Export

> **DEPRECATED**: This plugin has been superseded by native Claude Code features.
> See [Migration Guide](#migration-guide) below for instructions on switching to native settings.

[![Deprecated](https://img.shields.io/badge/status-deprecated-red)](#migration-guide)
[![Version](https://img.shields.io/github/v/tag/kenryu42/claude-code-plan-export?label=version&color=blue)](https://github.com/kenryu42/claude-code-plan-export)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Auto-export your Claude Code plans to the project root when you finish planning.

## Deprecation Notice

**This plugin is no longer maintained.** Claude Code now natively supports:

- **`planDirectory` setting** - Configure where plans are saved directly in Claude Code settings
- **Fresh context on plan execution** - Claude Code automatically clears context when executing a plan

These native features replace all functionality provided by this plugin. Please migrate to the native settings.

## Migration Guide

### Step 1: Uninstall the Plugin

```
/plugin uninstall plan-export
```

### Step 2: Configure Native Plan Directory

Add to your Claude Code settings (`.claude/settings.json` or via `/config`):

```json
{
  "planDirectory": "./plans"
}
```

Plans will now be saved directly to your configured directory.

### Step 3: Use Native Plan Execution

When you execute a plan, Claude Code now offer an option to start with a fresh context window. No need for manual `/clear` or `/new` commands.

### Feature Comparison

| This Plugin | Native Claude Code |
|-------------|-------------------|
| Session hooks to export plans | `planDirectory` setting |
| `/execute-plan` + manual `/clear` | Plan execution auto-clears context |
| `/export-project-plans` | Plans saved automatically |

---

<details>
<summary><strong>Legacy Documentation</strong> (click to expand)</summary>

## Why Use This Plugin?

- **Optimize token usage** - Plan with Opus, execute with faster/cheaper models
- **Clean implementation context** - Fresh context window without planning artifacts
- **Flexible workflows** - Execute plans with any model, not just Claude Code
- **Zero passive cost** - No MCP servers or Skills overhead

## Quick Start

### Installation

```
/plugin marketplace add kenryu42/cc-marketplace
/plugin install plan-export@cc-marketplace
```

> **Note:** Restart Claude Code after installation.

### Auto-Update

1. Run `/plugin` → Select `Marketplaces` → Choose `cc-marketplace` → Enable auto-update

### Usage

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────┐     ┌────────────────┐
│  1. Plan Mode   │────▶│ 2. Press ESC │────▶│ 3. /clear or │────▶│ 4. plan-{slug} │
│                 │     │              │     │    /new      │     │    .md saved!  │
└─────────────────┘     └──────────────┘     └──────────────┘     └────────────────┘
```

1. Plan with any model in Plan Mode
2. Press **ESC** when asked to choose auto-accept/manual
3. Start new session (`/clear`, `/reset`, or `/new`)
4. Plan exported to `plan-{slug}.md`

Then run `/execute-plan` to execute with your preferred model.

## Commands

| Command | Description | Output |
|---------|-------------|--------|
| `/execute-plan` | Execute most recent plan | Runs `*plan-*.md` in CWD |
| `/export-project-plans` | Export all project plans | Root (1) or `plans/` (2+) |
| `/export-project-plans-with-timestamp` | Export with timestamps | `YYYYMMDD-HHMMSS-plan-{slug}.md` |

## How It Works

```
SessionStart Hook              SessionEnd Hook
      │                              │
      ▼                              ▼
┌────────────────┐           ┌────────────────┐
│session_start.py│           │ export_plan.py │
│                │           │                │
│ Saves          │  ──────▶  │ Reads transcript│
│ TRANSCRIPT_DIR │  session  │ Finds slug     │
│ to env file    │           │ Copies plan    │
└────────────────┘           └────────────────┘
```

**Key paths:**
- Source: `~/.claude/plans/{slug}.md`
- Destination: `{CWD}/plan-{slug}.md`

## Folder Organization

```
1 plan found?  ──▶  Export to project root: plan-{slug}.md
2+ plans found? ──▶  Export to plans/ folder: plans/plan-{slug}.md
```

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
  execute-plan.md
  export-project-plans.md
  export-project-plans-with-timestamp.md
tests/
  test_export_plan.py
  test_export_project_plans.py
  test_concurrency.py
  test_session_start.py
```

## Development

```bash
# Setup
just setup          # Or: uv sync && uv run pre-commit install

# Test
uv run pytest

# Lint
just check          # Or: uv run ruff check && uv run mypy .
```

## License

MIT

</details>
