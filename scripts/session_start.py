#!/usr/bin/env python3
"""
Export transcript_path from stdin JSON to CLAUDE_ENV_FILE.

Called on SessionStart hook to make transcript path available to other hooks.
"""

import fcntl
import json
import os
import shlex
import sys


def main() -> int:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        print("CLAUDE_ENV_FILE not set, skipping", file=sys.stderr)
        return 0

    print(f"CLAUDE_ENV_FILE: {env_file}", file=sys.stderr)

    raw_input = sys.stdin.read()
    try:
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        return 1

    transcript_path = input_data.get("transcript_path")
    if not transcript_path:
        print("No transcript_path in input", file=sys.stderr)
        return 1

    if not isinstance(transcript_path, str):
        print(
            f"transcript_path must be a string, got {type(transcript_path).__name__}",
            file=sys.stderr,
        )
        return 1

    transcript_dir = os.path.abspath(os.path.dirname(transcript_path) or ".")

    if not os.path.isdir(transcript_dir):
        print(f"Transcript directory does not exist: {transcript_dir}", file=sys.stderr)
        return 1

    try:
        with open(env_file, "a", encoding="utf-8") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            f.write(f"export TRANSCRIPT_DIR={shlex.quote(transcript_dir)}\n")
    except (OSError, IOError) as e:
        print(f"Error writing to env file: {e}", file=sys.stderr)
        return 1

    print(f"Exported TRANSCRIPT_DIR={transcript_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
