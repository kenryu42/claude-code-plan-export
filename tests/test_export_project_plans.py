"""Tests for scripts/export_project_plans.py."""

# ruff: noqa: E402

import json
import os
import sys
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import export_project_plans
from tests import TempDirTestCase


class FindSlugsTests(TempDirTestCase):
    def test_ignores_malformed_lines_but_keeps_valid_slugs(self) -> None:
        transcript = self.tmpdir / "t.jsonl"
        transcript.write_text(
            "not json\n" + json.dumps({"slug": "ok"}), encoding="utf-8"
        )
        self.assertEqual(
            export_project_plans.find_slugs_in_transcript(transcript), {"ok"}
        )

    def test_missing_transcript_file_returns_empty_set(self) -> None:
        transcript = self.tmpdir / "missing.jsonl"
        slugs = export_project_plans.find_slugs_in_transcript(transcript)
        self.assertEqual(slugs, set())

    def test_collects_unique_slugs(self) -> None:
        transcript = self.tmpdir / "t.jsonl"
        transcript.write_text(
            "\n".join(
                [
                    json.dumps({"slug": "one"}),
                    json.dumps({"slug": "one"}),
                    json.dumps({"slug": "two"}),
                ]
            ),
            encoding="utf-8",
        )

        slugs = export_project_plans.find_slugs_in_transcript(transcript)
        self.assertEqual(slugs, {"one", "two"})


class ExportProjectPlansMainTests(TempDirTestCase):
    def test_missing_env_var_returns_error(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = export_project_plans.main()

        self.assertEqual(result, 1)

    def test_invalid_transcript_directory(self) -> None:
        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(self.tmpdir / "missing")}, clear=True
        ):
            result = export_project_plans.main()

        self.assertEqual(result, 1)

    def test_exports_multiple_plan_files_skipping_agent_transcripts(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()

        transcript_a = transcript_dir / "a.jsonl"
        transcript_b = transcript_dir / "agent-ignored.jsonl"

        transcript_a.write_text(
            "\n".join(
                [
                    json.dumps({"slug": "one"}),
                    json.dumps({"slug": "two"}),
                ]
            ),
            encoding="utf-8",
        )

        transcript_b.write_text(json.dumps({"slug": "ignored"}), encoding="utf-8")

        (plans_dir / "one.md").write_text("plan one", encoding="utf-8")
        (plans_dir / "two.md").write_text("plan two", encoding="utf-8")

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans.main()

        self.assertEqual(result, 0)
        exported_one = project_dir / "plan-one.md"
        exported_two = project_dir / "plan-two.md"

        self.assertTrue(exported_one.exists())
        self.assertTrue(exported_two.exists())
        self.assertEqual(exported_one.read_text(encoding="utf-8"), "plan one")
        self.assertEqual(exported_two.read_text(encoding="utf-8"), "plan two")

    def test_no_slugs_in_any_file_returns_zero(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()
        home_dir = self.tmpdir / "home"
        (home_dir / ".claude" / "plans").mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(
            json.dumps({"message": "none"}), encoding="utf-8"
        )

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans.main()

        self.assertEqual(result, 0)
        self.assertFalse(any(project_dir.glob("plan-*.md")))

    def test_missing_plan_file_is_skipped(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()
        home_dir = self.tmpdir / "home"
        (home_dir / ".claude" / "plans").mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(
            json.dumps({"slug": "missing"}), encoding="utf-8"
        )

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans.main()

        self.assertEqual(result, 0)
        self.assertFalse((project_dir / "plan-missing.md").exists())

    def test_copy_io_error_logs_and_continues(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()
        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(
            json.dumps({"slug": "fail"}) + "\n" + json.dumps({"slug": "succeed"}),
            encoding="utf-8",
        )

        (plans_dir / "fail.md").write_text("plan fail", encoding="utf-8")
        (plans_dir / "succeed.md").write_text("plan succeed", encoding="utf-8")

        original_copy2 = __import__("shutil").copy2

        def mock_copy2(src, dst):
            if "fail" in str(src):
                raise IOError("disk full")
            return original_copy2(src, dst)

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    with mock.patch("shutil.copy2", side_effect=mock_copy2):
                        result = export_project_plans.main()

        # Should return 0 (logs error but continues)
        self.assertEqual(result, 0)
        # Succeed file should be copied
        self.assertTrue((project_dir / "plan-succeed.md").exists())
        # Fail file should NOT be copied
        self.assertFalse((project_dir / "plan-fail.md").exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
