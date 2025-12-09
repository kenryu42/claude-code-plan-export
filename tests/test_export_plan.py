import io
import json
import sys
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import export_plan
from tests import TempDirTestCase


class FindSlugTests(TempDirTestCase):
    def test_valid_jsonl_with_slug(self) -> None:
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text("\n".join([
            json.dumps({"message": "hello"}),
            json.dumps({"slug": "abc123"}),
        ]), encoding="utf-8")

        slug = export_plan.find_slug_in_transcript(transcript)
        self.assertEqual(slug, "abc123")

    def test_no_slug_returns_none(self) -> None:
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"message": "hello"}), encoding="utf-8")

        slug = export_plan.find_slug_in_transcript(transcript)
        self.assertIsNone(slug)

    def test_empty_file_returns_none(self) -> None:
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text("", encoding="utf-8")

        slug = export_plan.find_slug_in_transcript(transcript)
        self.assertIsNone(slug)

    def test_malformed_lines_are_ignored(self) -> None:
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text("\n".join([
            "not json",
            json.dumps({"slug": "good"}),
        ]), encoding="utf-8")

        slug = export_plan.find_slug_in_transcript(transcript)
        self.assertEqual(slug, "good")


class FindSlugRetryTests(TempDirTestCase):
    def test_missing_transcript_file_returns_none(self) -> None:
        transcript = self.tmpdir / "missing.jsonl"

        slug = export_plan.find_slug_in_transcript(transcript)
        self.assertIsNone(slug)

    def test_retry_success_after_initial_no_slug(self) -> None:
        """Test that retries can find a slug that appears after initial scan."""
        transcript = self.tmpdir / "transcript.jsonl"
        # Start with no slug
        transcript.write_text(json.dumps({"message": "hello"}), encoding="utf-8")

        call_count = [0]
        original_open = open

        def mock_open_with_delayed_slug(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                # On second+ read, add the slug
                transcript.write_text(
                    json.dumps({"message": "hello"}) + "\n" + json.dumps({"slug": "found"}),
                    encoding="utf-8",
                )
            return original_open(*args, **kwargs)

        with mock.patch("builtins.open", side_effect=mock_open_with_delayed_slug):
            slug = export_plan.find_slug_in_transcript(transcript, retries=3, delay=0.01)

        self.assertEqual(slug, "found")


class ExportPlanMainTests(TempDirTestCase):
    def test_invalid_json_input_returns_error(self) -> None:
        with mock.patch("sys.stdin", io.StringIO("{bad")):
            result = export_plan.main()
        self.assertEqual(result, 1)

    def test_missing_transcript_file_returns_zero(self) -> None:
        transcript = self.tmpdir / "missing.jsonl"
        with mock.patch("sys.stdin", io.StringIO(json.dumps({"transcript_path": str(transcript)}))):
            result = export_plan.main()
        self.assertEqual(result, 0)

    def test_copy_io_error_returns_one(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()
        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        slug = "abc123"
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": slug}), encoding="utf-8")
        (plans_dir / f"{slug}.md").write_text("plan", encoding="utf-8")

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("shutil.copy2", side_effect=OSError("disk full")):
                    with mock.patch("sys.stdin", io.StringIO(json.dumps({"transcript_path": str(transcript)}))):
                        result = export_plan.main()

        self.assertEqual(result, 1)

    def test_first_slug_wins_when_multiple_present(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        first_slug = "first"
        second_slug = "second"
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(
            json.dumps({"slug": first_slug}) + "\n" + json.dumps({"slug": second_slug}),
            encoding="utf-8",
        )

        (plans_dir / f"{first_slug}.md").write_text("plan first", encoding="utf-8")
        (plans_dir / f"{second_slug}.md").write_text("plan second", encoding="utf-8")

        input_data = {"transcript_path": str(transcript)}

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                    result = export_plan.main()

        self.assertEqual(result, 0)
        # First slug wins - only first plan should be copied
        dest_file = project_dir / f"plan-{first_slug}.md"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(encoding="utf-8"), "plan first")
        # Second slug file should NOT exist
        self.assertFalse((project_dir / f"plan-{second_slug}.md").exists())

    def test_full_flow_copies_plan_file(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"
        plans_dir = home_dir / ".claude" / "plans"
        plans_dir.mkdir(parents=True)

        slug = "abc123"
        plan_content = "plan contents"
        plan_file = plans_dir / f"{slug}.md"
        plan_file.write_text(plan_content, encoding="utf-8")

        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": slug}), encoding="utf-8")

        input_data = {"transcript_path": str(transcript)}

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                    result = export_plan.main()

        self.assertEqual(result, 0)
        dest_file = project_dir / f"plan-{slug}.md"
        self.assertTrue(dest_file.exists())
        self.assertEqual(dest_file.read_text(encoding="utf-8"), plan_content)

    def test_missing_transcript_path(self) -> None:
        with mock.patch("sys.stdin", io.StringIO(json.dumps({}))):
            result = export_plan.main()

        self.assertEqual(result, 1)

    def test_missing_plan_file_returns_zero(self) -> None:
        project_dir = self.tmpdir / "project"
        project_dir.mkdir()

        home_dir = self.tmpdir / "home"

        slug = "abc123"
        transcript = self.tmpdir / "transcript.jsonl"
        transcript.write_text(json.dumps({"slug": slug}), encoding="utf-8")

        input_data = {"transcript_path": str(transcript)}

        with mock.patch("pathlib.Path.home", return_value=home_dir):
            with mock.patch("pathlib.Path.cwd", return_value=project_dir):
                with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                    result = export_plan.main()

        self.assertEqual(result, 0)
        self.assertFalse((project_dir / f"plan-{slug}.md").exists())


if __name__ == "__main__":
    import unittest
    unittest.main()
