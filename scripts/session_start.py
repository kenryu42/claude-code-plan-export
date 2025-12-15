#!/usr/bin/env python3
"""
Export transcript_path from stdin JSON to CLAUDE_ENV_FILE.

Called on SessionStart hook to make transcript path available to other hooks.
"""

import json
import os
import sys
import fcntl
import threading


_ENV_FILE_LOCK = threading.Lock()


def main() -> int:
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file:
        print("CLAUDE_ENV_FILE not set, skipping", file=sys.stderr)
        return 0

    print(f"CLAUDE_ENV_FILE: {env_file}", file=sys.stderr)

    with _ENV_FILE_LOCK:
        raw_input = sys.stdin.read()
        if not raw_input and hasattr(sys.stdin, "seek"):
            try:
                sys.stdin.seek(0)
                raw_input = sys.stdin.read()
            except Exception:
                pass

        try:
            input_data = json.loads(raw_input)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON input: {e}", file=sys.stderr)
            return 0

        transcript_path = input_data.get("transcript_path")
        if not transcript_path:
            print("No transcript_path in input", file=sys.stderr)
            return 0

        with open(env_file, "a", encoding="utf-8") as f:
            try:
                fcntl.flock(f.fileno(), fcntl.LOCK_EX)
                f.write(
                    f'export TRANSCRIPT_DIR="{os.path.dirname(transcript_path)}"\n'
                )
            finally:
                try:
                    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                except OSError:
                    pass

    print(f"Exported TRANSCRIPT_DIR={os.path.dirname(transcript_path)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
