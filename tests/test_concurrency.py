"""Concurrency-related tests."""

import io
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from pathlib import Path
from unittest import mock

from scripts import export_plan

from . import TempDirTestCase

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"


class ConcurrencyTests(TempDirTestCase):
    def test_env_file_concurrent_writes(self) -> None:
        """
        Test that concurrent process invocations write to env file without
        corruption.
        """
        env_file = self.tmpdir / "env.sh"
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": "s"}), encoding="utf-8")

        input_json = json.dumps({"transcript_path": str(transcript)})
        script_path = SCRIPTS_DIR / "session_start.py"

        def run_script():
            result = subprocess.run(
                [sys.executable, str(script_path)],
                input=input_json,
                capture_output=True,
                text=True,
                env={**os.environ, "CLAUDE_ENV_FILE": str(env_file)},
            )
            return result.returncode

        # Start both processes and wait for them
        barrier = threading.Barrier(2)
        results = []

        def worker():
            barrier.wait()
            results.append(run_script())

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Both should succeed
        self.assertEqual(results, [0, 0])

        content = env_file.read_text(encoding="utf-8") if env_file.exists() else ""
        lines = [line for line in content.splitlines() if line]
        transcript_dir = os.path.dirname(str(transcript))
        expected_line = f"export TRANSCRIPT_DIR={shlex.quote(transcript_dir)}"
        self.assertEqual(lines, [expected_line, expected_line])

    def test_concurrent_same_slug_copy(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        slug = "shared"
        plan_file = plans_dir / f"{slug}.md"
        plan_file.write_text("base", encoding="utf-8")

        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": slug}), encoding="utf-8")

        contents = ["content-one", "content-two"]
        start_barrier = threading.Barrier(len(contents))
        thread_local = threading.local()

        def slow_copy(src, dst, *, follow_symlinks=True):
            data = thread_local.content
            dest_path = Path(dst)
            with open(dest_path, "w", encoding="utf-8") as f:
                mid = max(1, len(data) // 2)
                f.write(data[:mid])
                f.flush()
                time.sleep(0.02)
                f.write(data[mid:])
            return dest_path

        def worker(content: str):
            thread_local.content = content
            with mock.patch(
                "sys.stdin",
                io.StringIO(json.dumps({"transcript_path": str(transcript)})),
            ):
                start_barrier.wait()
                export_plan.main()

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("shutil.copy2", side_effect=slow_copy):
                    threads = [
                        threading.Thread(target=worker, args=(c,)) for c in contents
                    ]
                    for t in threads:
                        t.start()
                    for t in threads:
                        t.join()

        dest_file = project_dir / f"plan-{slug}.md"
        dest_content = (
            dest_file.read_text(encoding="utf-8") if dest_file.exists() else ""
        )
        self.assertIn(dest_content, contents)

    def test_read_while_write_returns_slug(self) -> None:
        transcript = self.tmpdir / "transcript.jsonl"

        start_barrier = threading.Barrier(2)
        partial_written = threading.Event()
        slug_line = json.dumps({"slug": "late"})

        def writer():
            start_barrier.wait()
            with open(transcript, "w", encoding="utf-8") as f:
                mid = len(slug_line) // 2
                f.write(slug_line[:mid])
                f.write("\n")
                f.flush()
                partial_written.set()
                time.sleep(0.05)
                f.write(slug_line)
                f.write("\n")
                f.flush()

        writer_thread = threading.Thread(target=writer)
        writer_thread.start()

        start_barrier.wait()
        partial_written.wait()
        slug = export_plan.find_slug_in_transcript(transcript)
        writer_thread.join()

        self.assertEqual(slug, "late")

    def test_toctou_file_deletion(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        slug = "fragile"
        plan_file = plans_dir / f"{slug}.md"
        plan_file.write_text("content", encoding="utf-8")

        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": slug}), encoding="utf-8")

        input_data = {"transcript_path": str(transcript)}

        def disappearing_copy(src, dst, *, follow_symlinks=True):
            Path(src).unlink(missing_ok=True)
            raise FileNotFoundError(src)

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("shutil.copy2", side_effect=disappearing_copy):
                    with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                        result = export_plan.main()

        self.assertEqual(result, 0)


if __name__ == "__main__":
    import unittest

    unittest.main()
