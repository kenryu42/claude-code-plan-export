"""Tests for scripts/session_start.py."""

# ruff: noqa: E402

import io
import json
import os
import shlex
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

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                result = session_start.main()

        self.assertEqual(result, 0)
        content = env_file.read_text(encoding="utf-8")
        transcript_dir = os.path.dirname(str(transcript))
        expected = f"export TRANSCRIPT_DIR={shlex.quote(transcript_dir)}\n"
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

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO("{invalid")):
                result = session_start.main()

        self.assertEqual(result, 1)
        self.assertFalse(env_file.exists())

    def test_missing_transcript_path_field(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO(json.dumps({}))):
                result = session_start.main()

        self.assertEqual(result, 1)
        self.assertFalse(env_file.exists())

    def test_empty_stdin_returns_error(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO("")):
                result = session_start.main()

        self.assertEqual(result, 1)
        self.assertFalse(env_file.exists())

    def test_non_string_transcript_path_returns_error(self) -> None:
        env_file = self.tmpdir / "env.sh"

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch(
                "sys.stdin", io.StringIO(json.dumps({"transcript_path": 12345}))
            ):
                result = session_start.main()

        self.assertEqual(result, 1)
        self.assertFalse(env_file.exists())

    def test_unwritable_env_file_returns_error(self) -> None:
        # Create a directory where we want the file - can't write a file with same name
        env_file = self.tmpdir / "unwritable" / "env.sh"
        # Don't create parent directory, so write will fail

        # Transcript must be in an existing directory
        transcript = self.tmpdir / "transcript.jsonl"
        input_data = {"transcript_path": str(transcript)}

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                result = session_start.main()

        self.assertEqual(result, 1)

    def test_nonexistent_transcript_dir_returns_error(self) -> None:
        env_file = self.tmpdir / "env.sh"
        # Transcript in a directory that doesn't exist
        transcript = self.tmpdir / "nonexistent" / "transcript.jsonl"
        input_data = {"transcript_path": str(transcript)}

        with mock.patch.dict(
            os.environ, {"CLAUDE_ENV_FILE": str(env_file)}, clear=True
        ):
            with mock.patch("sys.stdin", io.StringIO(json.dumps(input_data))):
                result = session_start.main()

        self.assertEqual(result, 1)
        self.assertFalse(env_file.exists())


if __name__ == "__main__":
    import unittest

    unittest.main()
