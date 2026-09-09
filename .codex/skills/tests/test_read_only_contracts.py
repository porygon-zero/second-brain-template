#!/usr/bin/env python3
"""Keep read-only role enforcement aligned across supported runtimes."""

from __future__ import annotations

import unittest
from pathlib import Path


VAULT = Path(__file__).resolve().parents[3]


class ReadOnlyContractTests(unittest.TestCase):
    def test_expert_requires_claim_level_provenance(self) -> None:
        skill = (VAULT / ".codex" / "skills" / "second-brain-expert" / "SKILL.md").read_text(encoding="utf-8")
        reference = (VAULT / ".codex" / "skills" / "second-brain-expert" / "references" / "retrieval-and-answering.md").read_text(encoding="utf-8")
        disclosure = "No material vault knowledge was found for this question; the following is a general-knowledge answer."

        for text in (skill, reference):
            self.assertIn(disclosure, text)
            self.assertIn("incidental", text)
            self.assertIn("contextual", text)
            self.assertIn("material", text)

    def test_opencode_read_only_agents_deny_mutating_tools(self) -> None:
        for role in ("second-brain-expert", "second-brain-interlocutor"):
            text = (VAULT / ".opencode" / "agents" / f"{role}.md").read_text(
                encoding="utf-8"
            )
            with self.subTest(role=role):
                self.assertIn("edit: deny", text)
                self.assertIn("bash: deny", text)

    def test_codex_read_only_skills_reference_verified_launcher(self) -> None:
        for role in ("second-brain-expert", "second-brain-interlocutor"):
            text = (VAULT / ".codex" / "skills" / role / "SKILL.md").read_text(
                encoding="utf-8"
            )
            with self.subTest(role=role):
                self.assertIn("run_read_only_agent.py", text)
                self.assertIn("verify it is unchanged", text)

    def test_roles_share_artifact_development_contract(self) -> None:
        protocol = VAULT / ".codex" / "skills" / "artifact-development.md"
        self.assertTrue(protocol.is_file())
        protocol_text = protocol.read_text(encoding="utf-8")
        for phrase in (
            "Delegated production",
            "Collaborative development",
            "Mixed mode",
            "Treat sufficient context",
            "does not authorize saving",
        ):
            self.assertIn(phrase, protocol_text)

        for role in (
            "second-brain-expert",
            "second-brain-interlocutor",
            "second-brain-librarian",
        ):
            text = (VAULT / ".codex" / "skills" / role / "SKILL.md").read_text(
                encoding="utf-8"
            )
            with self.subTest(role=role):
                self.assertIn("artifact-development.md", text)


if __name__ == "__main__":
    unittest.main()
