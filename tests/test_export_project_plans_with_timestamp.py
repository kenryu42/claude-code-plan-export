"""Tests for scripts/export_project_plans_with_timestamp.py."""

# ruff: noqa: E402

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import export_project_plans_with_timestamp
from tests import TempDirTestCase


class GetFileTimestampTests(TempDirTestCase):
    def test_timestamp_format(self) -> None:
        f = self.tmpdir / "plan.md"
        f.write_text("x", encoding="utf-8")
        ts = 1735689600  # 2025-01-01 00:00:00 local time, depending on timezone
        os.utime(f, (ts, ts))

        stamp = export_project_plans_with_timestamp.get_file_timestamp(f)

        self.assertRegex(stamp, r"^\d{8}-\d{2}:\d{2}:\d{2}$")
        self.assertEqual(stamp, datetime.fromtimestamp(ts).strftime("%Y%m%d-%H:%M:%S"))


class ExportWithTimestampMainTests(TempDirTestCase):
    def test_missing_env_var_returns_error(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            result = export_project_plans_with_timestamp.main()
        self.assertEqual(result, 1)

    def test_invalid_transcript_directory(self) -> None:
        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(self.tmpdir / "missing")}, clear=True
        ):
            result = export_project_plans_with_timestamp.main()
        self.assertEqual(result, 1)

    def test_single_file_exports_to_cwd_not_plans_folder(self) -> None:
        """When only one plan file exists, it should go to cwd, not plans/."""
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(
            json.dumps({"slug": "one"}), encoding="utf-8"
        )

        plan_file = plans_dir / "one.md"
        plan_file.write_text("plan one", encoding="utf-8")

        ts = 1735689600
        os.utime(plan_file, (ts, ts))
        expected_prefix = datetime.fromtimestamp(ts).strftime("%Y%m%d-%H:%M:%S")

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        # Single file should be in cwd, not plans/ folder
        exported = project_dir / f"{expected_prefix}-plan-one.md"
        self.assertTrue(exported.exists())
        self.assertFalse((project_dir / "plans").exists())
        self.assertEqual(exported.read_text(encoding="utf-8"), "plan one")

    def test_multiple_files_export_to_plans_folder(self) -> None:
        """When 2+ plan files exist, they should go to plans/ folder."""
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(
            json.dumps({"slug": "one"}) + "\n" + json.dumps({"slug": "two"}),
            encoding="utf-8",
        )

        plan_one = plans_dir / "one.md"
        plan_two = plans_dir / "two.md"
        plan_one.write_text("plan one", encoding="utf-8")
        plan_two.write_text("plan two", encoding="utf-8")

        ts_one = 1735689600
        ts_two = 1735689700
        os.utime(plan_one, (ts_one, ts_one))
        os.utime(plan_two, (ts_two, ts_two))
        prefix_one = datetime.fromtimestamp(ts_one).strftime("%Y%m%d-%H:%M:%S")
        prefix_two = datetime.fromtimestamp(ts_two).strftime("%Y%m%d-%H:%M:%S")

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        # Multiple files should be in plans/ folder
        self.assertTrue((project_dir / "plans").is_dir())
        exported_one = project_dir / "plans" / f"{prefix_one}-plan-one.md"
        exported_two = project_dir / "plans" / f"{prefix_two}-plan-two.md"
        self.assertTrue(exported_one.exists())
        self.assertTrue(exported_two.exists())
        self.assertEqual(exported_one.read_text(encoding="utf-8"), "plan one")
        self.assertEqual(exported_two.read_text(encoding="utf-8"), "plan two")
        # Should NOT be in project root
        self.assertFalse(any(project_dir.glob("*-plan-one.md")))
        self.assertFalse(any(project_dir.glob("*-plan-two.md")))

    def test_skips_agent_transcripts(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()

        (transcript_dir / "agent-ignored.jsonl").write_text(
            json.dumps({"slug": "ignored"}), encoding="utf-8"
        )
        (plans_dir / "ignored.md").write_text("plan ignored", encoding="utf-8")

        with mock.patch.dict(
            os.environ, {"TRANSCRIPT_DIR": str(transcript_dir)}, clear=True
        ):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        self.assertFalse(any(project_dir.glob("*-plan-ignored.md")))

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
                    result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        self.assertFalse(any(project_dir.glob("*-plan-missing.md")))

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

        plan_fail = plans_dir / "fail.md"
        plan_succeed = plans_dir / "succeed.md"
        plan_fail.write_text("plan fail", encoding="utf-8")
        plan_succeed.write_text("plan succeed", encoding="utf-8")

        ts_fail = 1735689600
        ts_succeed = 1735689700
        os.utime(plan_fail, (ts_fail, ts_fail))
        os.utime(plan_succeed, (ts_succeed, ts_succeed))

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
                        result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        # Files should be in plans/ folder since 2 valid files
        self.assertFalse(any((project_dir / "plans").glob("*-plan-fail.md")))
        self.assertTrue(any((project_dir / "plans").glob("*-plan-succeed.md")))


if __name__ == "__main__":
    import unittest

    unittest.main()
