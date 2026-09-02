#!/usr/bin/env python3
"""Tests for the Codex read-only role launcher."""

from __future__ import annotations

import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SKILLS = Path(__file__).resolve().parents[1]
SCRIPT = SKILLS / "run_read_only_agent.py"
SPEC = importlib.util.spec_from_file_location("run_read_only_agent", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ReadOnlyAgentTests(unittest.TestCase):
    def test_snapshot_detects_tracked_and_untracked_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory)
            subprocess.run(["git", "init"], cwd=vault, check=True, capture_output=True)
            subprocess.run(
                ["git", "config", "user.email", "test@example.invalid"],
                cwd=vault,
                check=True,
            )
            subprocess.run(
                ["git", "config", "user.name", "Test"], cwd=vault, check=True
            )
            tracked = vault / "tracked.md"
            tracked.write_text("original\n", encoding="utf-8")
            subprocess.run(["git", "add", "tracked.md"], cwd=vault, check=True)
            subprocess.run(
                ["git", "commit", "-m", "fixture"],
                cwd=vault,
                check=True,
                capture_output=True,
            )

            baseline = RUNNER.repository_snapshot(vault)
            tracked.write_text("changed\n", encoding="utf-8")
            self.assertNotEqual(RUNNER.repository_snapshot(vault), baseline)

            tracked.write_text("original\n", encoding="utf-8")
            self.assertEqual(RUNNER.repository_snapshot(vault), baseline)
            (vault / "untracked.md").write_text("new\n", encoding="utf-8")
            self.assertNotEqual(RUNNER.repository_snapshot(vault), baseline)

    def test_codex_command_enforces_read_only_ephemeral_execution(self) -> None:
        with mock.patch.object(RUNNER, "resolve_codex", return_value="codex"):
            command = RUNNER.codex_command(Path("/vault"), "expert", "Audit this")

        self.assertIn("--ephemeral", command)
        self.assertEqual(command[command.index("--sandbox") + 1], "read-only")
        self.assertEqual(command[command.index("--ask-for-approval") + 1], "never")
        self.assertLess(command.index("--sandbox"), command.index("exec"))
        self.assertLess(command.index("--ask-for-approval"), command.index("exec"))
        self.assertIn("Use $second-brain-expert", command[-1])


if __name__ == "__main__":
    unittest.main()
