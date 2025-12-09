import io
import json
import os
import sys
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import session_start
from tests import TempDirTestCase


class SessionStartTests(TempDirTestCase):
    def test_valid_json_writes_env_line(self) -> None:
        env_file = self.tmpdir / "env.sh"
        transcript = self.tmpdir / "transcript.jsonl"
        input_data = {"transcript_path": str(transcript)}

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                result = session_start.main()

        self.assertEqual(result, 0)
        content = env_file.read_text(encoding="utf-8")
        expected = f'export TRANSCRIPT_PATH="{os.path.dirname(str(transcript))}"\n'
        self.assertEqual(content, expected)

    def test_missing_env_var_skips_write(self) -> None:
        env_file = self.tmpdir / "env.sh"
        input_data = {"transcript_path": str(self.tmpdir / "transcript.jsonl")}

        with mock.patch.dict(os.environ, {}, clear=True):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                result = session_start.main()

        self.assertEqual(result, 0)
        self.assertFalse(env_file.exists())

    def test_invalid_json_input(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO("{invalid")):
                result = session_start.main()

        self.assertEqual(result, 0)
        self.assertFalse(env_file.exists())

    def test_missing_transcript_path_field(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO(json.dumps({}))):
                result = session_start.main()

        self.assertEqual(result, 0)
        self.assertFalse(env_file.exists())

    def test_empty_stdin_skips_write(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO("")):
                result = session_start.main()

        self.assertEqual(result, 0)
        self.assertFalse(env_file.exists())

    def test_non_string_transcript_path_raises_type_error(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO(json.dumps({"transcript_path": 12345}))):
                # Code doesn't validate type - os.path.dirname expects str/bytes/PathLike
                with self.assertRaises(TypeError):
                    session_start.main()

    def test_unwritable_env_file_raises_error(self) -> None:
        # Create a directory where we want the file - can't write a file with same name
        env_file = self.tmpdir / "unwritable" / "env.sh"
        # Don't create parent directory, so write will fail

        transcript = self.tmpdir / "transcript.jsonl"
        input_data = {"transcript_path": str(transcript)}

        with mock.patch.dict(os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                # Should raise an error when trying to write to non-existent directory
                with self.assertRaises(FileNotFoundError):
                    session_start.main()


if __name__ == "__main__":
    import unittest
    unittest.main()
