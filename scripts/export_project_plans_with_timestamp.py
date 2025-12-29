#!/usr/bin/env python3
"""Export plan files with timestamp prefix from source file mtime.

Scans all transcript JSONL files in TRANSCRIPT_DIR (excluding agent-* files),
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
    """Get file mtime formatted as YYYYMMDD-HHMMSS."""
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y%m%d-%H%M%S")


def main() -> int:
    # 1. Get TRANSCRIPT_DIR env variable
    transcript_dir = os.environ.get("TRANSCRIPT_DIR")
    if not transcript_dir:
        print("TRANSCRIPT_DIR environment variable is not set", file=sys.stderr)
        return 1

    transcript_path = Path(transcript_dir)
    if not transcript_path.is_dir():
        print(f"TRANSCRIPT_DIR is not a directory: {transcript_dir}", file=sys.stderr)
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

    # 3. Collect valid plan files
    plans_source_dir = Path.home() / ".claude" / "plans"
    valid_files: list[tuple[str, Path]] = []

    for slug in sorted(all_slugs):
        source_file = plans_source_dir / f"{slug}.md"

        if not source_file.exists():
            print(
                f"Plan file not found for slug '{slug}': {source_file}", file=sys.stderr
            )
            continue

        valid_files.append((slug, source_file))

    # 4. Copy plan files (use plans/ folder only if more than one file)
    copied = 0
    use_plans_folder = len(valid_files) > 1
    plans_dest_dir = Path.cwd() / "plans"

    if use_plans_folder and not plans_dest_dir.exists():
        plans_dest_dir.mkdir(parents=True)

    for slug, source_file in valid_files:
        timestamp = get_file_timestamp(source_file)
        if use_plans_folder:
            dest_file = plans_dest_dir / f"{timestamp}-plan-{slug}.md"
        else:
            dest_file = Path.cwd() / f"{timestamp}-plan-{slug}.md"

        try:
            shutil.copy2(source_file, dest_file)
            print(f"Copied: {dest_file}")
            copied += 1
        except OSError as e:
            print(f"Error copying {source_file}: {e}", file=sys.stderr)

    print(f"Exported {copied} plan file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
