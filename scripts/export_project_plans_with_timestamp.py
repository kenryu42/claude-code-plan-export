#!/usr/bin/env python3
"""Export plan files with timestamp prefix from source file mtime.

Scans all transcript JSONL files in TRANSCRIPT_PATH (excluding agent-* files),
extracts plan slugs, and copies the corresponding plan files from
~/.claude/plans/ to the project root as:

    YYYYMMDD-HHMMSS-plan-{slug}.md
"""

import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

try:
    # When executed as a script from within scripts/
    from export_project_plans import find_slugs_in_transcript
except ModuleNotFoundError:  # pragma: no cover
    # When imported as scripts.export_project_plans_with_timestamp
    from scripts.export_project_plans import find_slugs_in_transcript


def get_file_timestamp(file_path: Path) -> str:
    """Get file mtime formatted as YYYYMMDD-HH:MM:SS."""
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y%m%d-%H:%M:%S")


def main() -> int:
    # 1. Get TRANSCRIPT_PATH env variable
    transcript_dir = os.environ.get("TRANSCRIPT_PATH")
    if not transcript_dir:
        print("TRANSCRIPT_PATH environment variable is not set", file=sys.stderr)
        return 1

    transcript_path = Path(transcript_dir)
    if not transcript_path.is_dir():
        print(f"TRANSCRIPT_PATH is not a directory: {transcript_dir}", file=sys.stderr)
        return 1

    # 2. Parse all JSONL files, skip agent-* files
    all_slugs: set[str] = set()
    for jsonl_file in transcript_path.glob("*.jsonl"):
        if jsonl_file.name.startswith("agent"):
            continue
        slugs = find_slugs_in_transcript(jsonl_file)
        all_slugs.update(slugs)

    if not all_slugs:
        print("No slugs found in any transcript files", file=sys.stderr)
        return 0

    # 3. Copy plan files to project root with timestamp prefix
    plans_dir = Path.home() / ".claude" / "plans"
    copied = 0

    for slug in sorted(all_slugs):
        source_file = plans_dir / f"{slug}.md"

        if not source_file.exists():
            print(f"Plan file not found for slug '{slug}': {source_file}", file=sys.stderr)
            continue

        timestamp = get_file_timestamp(source_file)
        dest_file = Path.cwd() / f"{timestamp}-plan-{slug}.md"

        try:
            shutil.copy2(source_file, dest_file)
            print(f"Copied: {dest_file}")
            copied += 1
        except IOError as e:
            print(f"Error copying {source_file}: {e}", file=sys.stderr)

    print(f"Exported {copied} plan file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
