---
description: Export project plans with timestamps to current directory
disable-model-invocation: true
allowed-tools: Bash
---

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/export_project_plans_with_timestamp.py > /dev/null 2>&1`

The execution of export_project_plans_with_timestamp.py is a background task and it is normal that you don't see the output.
The user expects nothing from you.
Just simply reply "export_project_plans_with_timestamp executed.". Nothing more.
