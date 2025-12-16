#!/usr/bin/env python3
"""
Copy plan markdown file from ~/.claude/plans/ to project root on session end.

Reads session info from stdin (JSON), parses the transcript JSONL to find
the plan slug, then copies the corresponding plan file.
"""

import json
import shutil
import sys
import time
from pathlib import Path


def find_slug_in_transcript(
    transcript_path: Path, *, retries: int = 5, delay: float = 0.05
) -> str | None:
    """Scan transcript JSONL for the first object containing a 'slug' field.

    Retries to handle concurrent writes that may temporarily produce malformed lines.
    """

    def _scan_once() -> str | None:
        try:
            with open(transcript_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        if "slug" in obj:
                            return obj["slug"]
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            print(f"Transcript file not found: {transcript_path}", file=sys.stderr)
            return None
        except OSError as e:
            print(f"Error reading transcript: {e}", file=sys.stderr)
            return None
        return None

    for attempt in range(max(1, retries)):
        slug = _scan_once()
        if slug:
            return slug
        if attempt < retries - 1:
            time.sleep(delay)
    return None


def main() -> int:
    # Read JSON from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON input: {e}", file=sys.stderr)
        return 1

    transcript_path = input_data.get("transcript_path")
    if not transcript_path:
        print("No transcript_path in input", file=sys.stderr)
        return 1

    # Find slug in transcript
    slug = find_slug_in_transcript(Path(transcript_path))
    if not slug:
        print("No slug found in transcript", file=sys.stderr)
        return 0

    # Build source and destination paths
    plans_dir = Path.home() / ".claude" / "plans"
    source_file = plans_dir / f"{slug}.md"
    dest_file = Path.cwd() / f"plan-{slug}.md"

    if not source_file.exists():
        print(f"Plan file not found: {source_file}", file=sys.stderr)
        return 0

    # Copy the file
    try:
        shutil.copy2(source_file, dest_file)
        print(f"Copied plan to {dest_file}")
    except FileNotFoundError:
        print(f"Error copying file: {source_file} not found", file=sys.stderr)
        return 0
    except OSError as e:
        print(f"Error copying file: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
