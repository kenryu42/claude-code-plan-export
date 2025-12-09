---
description: Export project plans to current directory
disable-model-invocation: true
allowed-tools: Bash
---

!`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/export_project_plans.py > /dev/null 2>&1`

The execution of export_project_plans.py is a background task and it is normal that you don't see the output.
The user expects nothing from you.
Just simply reply "export_project_plans executed.". Nothing more.
