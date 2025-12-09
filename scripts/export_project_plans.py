#!/usr/bin/env python3
"""
Export all plan markdown files from ~/.claude/plans/ to project root.

Scans all transcript JSONL files in TRANSCRIPT_PATH (excluding agent-* files),
extracts plan slugs, and copies the corresponding plan files.
"""

import json
import os
import shutil
import sys
from pathlib import Path


def find_slugs_in_transcript(transcript_path: Path) -> set[str]:
    """Scan transcript JSONL for all objects containing a 'slug' field."""
    slugs: set[str] = set()
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    if "slug" in obj:
                        slugs.add(obj["slug"])
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        print(f"Transcript file not found: {transcript_path}", file=sys.stderr)
    except IOError as e:
        print(f"Error reading transcript: {e}", file=sys.stderr)
    return slugs


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

    # 3. Copy plan files to project root
    plans_dir = Path.home() / ".claude" / "plans"
    copied = 0

    for slug in sorted(all_slugs):
        source_file = plans_dir / f"{slug}.md"
        dest_file = Path.cwd() / f"plan-{slug}.md"

        if not source_file.exists():
            print(f"Plan file not found for slug '{slug}': {source_file}", file=sys.stderr)
            continue

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
