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
        with mock.patch.dict(os.environ, {"TRANSCRIPT_PATH": str(self.tmpdir / "missing")}, clear=True):
            result = export_project_plans_with_timestamp.main()
        self.assertEqual(result, 1)

    def test_exports_with_correct_timestamp_prefix(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()
        (transcript_dir / "a.jsonl").write_text(json.dumps({"slug": "one"}), encoding="utf-8")

        plan_file = plans_dir / "one.md"
        plan_file.write_text("plan one", encoding="utf-8")

        ts = 1735689600
        os.utime(plan_file, (ts, ts))
        expected_prefix = datetime.fromtimestamp(ts).strftime("%Y%m%d-%H:%M:%S")

        with mock.patch.dict(os.environ, {"TRANSCRIPT_PATH": str(transcript_dir)}, clear=True):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        exported = project_dir / f"{expected_prefix}-plan-one.md"
        self.assertTrue(exported.exists())
        self.assertEqual(exported.read_text(encoding="utf-8"), "plan one")

    def test_skips_agent_transcripts(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        transcript_dir = self.tmpdir / "transcripts"
        transcript_dir.mkdir()

        (transcript_dir / "agent-ignored.jsonl").write_text(json.dumps({"slug": "ignored"}), encoding="utf-8")
        (plans_dir / "ignored.md").write_text("plan ignored", encoding="utf-8")

        with mock.patch.dict(os.environ, {"TRANSCRIPT_PATH": str(transcript_dir)}, clear=True):
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
        (transcript_dir / "a.jsonl").write_text(json.dumps({"slug": "missing"}), encoding="utf-8")

        with mock.patch.dict(os.environ, {"TRANSCRIPT_PATH": str(transcript_dir)}, clear=True):
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

        with mock.patch.dict(os.environ, {"TRANSCRIPT_PATH": str(transcript_dir)}, clear=True):
            with mock.patch("pathlib.Path.home", return_value=home_dir):
                with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                    with mock.patch("shutil.copy2", side_effect=mock_copy2):
                        result = export_project_plans_with_timestamp.main()

        self.assertEqual(result, 0)
        self.assertFalse(any(project_dir.glob("*-plan-fail.md")))
        self.assertTrue(any(project_dir.glob("*-plan-succeed.md")))


if __name__ == "__main__":
    import unittest

    unittest.main()
