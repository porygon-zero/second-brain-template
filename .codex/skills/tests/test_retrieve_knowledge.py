#!/usr/bin/env python3
"""Focused tests for Knowledge retrieval."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[1]
SCRIPT = SKILLS / "retrieve_knowledge.py"
FIXTURE_VAULT = Path(__file__).with_name("fixtures") / "retrieval-vault"

SPEC = importlib.util.spec_from_file_location("retrieve_knowledge", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
RETRIEVAL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RETRIEVAL)


class RetrievalTests(unittest.TestCase):
    def test_exact_title_precedes_exact_alias_and_malformed_note_is_skipped(self) -> None:
        packet = RETRIEVAL.retrieve(FIXTURE_VAULT, "AI Safety", limit=2)

        self.assertEqual(
            [candidate["title"] for candidate in packet["candidates"]],
            ["AI Safety", "Responsible Systems"],
        )
        self.assertEqual(packet["candidates"][0]["rationale"], ["exact title"])
        self.assertEqual(packet["candidates"][1]["rationale"], ["exact alias"])
        self.assertEqual(
            [warning["file"] for warning in packet["warnings"]],
            ["Knowledge/Broken.md", "Knowledge/Invalid Metadata.md"],
        )

    def test_summary_evidence_outranks_low_weight_full_body_fallback(self) -> None:
        oversight = RETRIEVAL.retrieve(FIXTURE_VAULT, "human oversight", limit=3)
        hidden = RETRIEVAL.retrieve(FIXTURE_VAULT, "burieduniqueterm", limit=3)

        self.assertEqual(oversight["candidates"][0]["title"], "Responsible Systems")
        self.assertIn("summary: human, oversight", oversight["candidates"][0]["rationale"])
        self.assertEqual(hidden["candidates"][0]["title"], "Hidden Body")
        self.assertIn("body: burieduniqueterm", hidden["candidates"][0]["rationale"])
        self.assertEqual(
            oversight["candidates"][0]["map_routing"],
            [{"domain": "artificial-intelligence", "hub_note": "AI Map"}],
        )

    def test_conservative_concept_morphology_matches_ism_and_ist(self) -> None:
        self.assertEqual(
            RETRIEVAL._matching_terms(["capitalism"], "capitalist competition"),
            ["capitalism"],
        )
        self.assertEqual(
            RETRIEVAL._matching_terms(["capitalist"], "capitalism and technology"),
            ["capitalist"],
        )

    def test_html_comments_do_not_match_or_leak_from_summaries(self) -> None:
        for hidden_term in (
            "hiddenuniqueterm",
            "hiddenmultiterm",
            "hiddenunclosedterm",
        ):
            with self.subTest(hidden_term=hidden_term):
                self.assertEqual(
                    RETRIEVAL.retrieve(FIXTURE_VAULT, hidden_term)["candidates"],
                    [],
                )

        packet = RETRIEVAL.retrieve(FIXTURE_VAULT, "visible signal remains searchable")
        self.assertEqual(packet["candidates"][0]["title"], "Commented Summary")
        self.assertEqual(
            packet["candidates"][0]["summary"],
            "Visible. Signal remains searchable.",
        )

        text_packet = RETRIEVAL.render_text(packet)
        json_packet = json.dumps(packet, ensure_ascii=False, sort_keys=True)
        for output in (text_packet, json_packet):
            self.assertNotIn("<!--", output)
            self.assertNotIn("-->", output)
            self.assertNotIn("hiddenuniqueterm", output)
            self.assertNotIn("hiddenmultiterm", output)
            self.assertNotIn("author-only guidance", output)

    def test_unclosed_html_comment_hides_the_rest_of_the_summary(self) -> None:
        packet = RETRIEVAL.retrieve(FIXTURE_VAULT, "safe prefix")

        self.assertEqual(packet["candidates"][0]["title"], "Unclosed Comment")
        self.assertEqual(packet["candidates"][0]["summary"], "Safe prefix")
        self.assertNotIn("hiddenunclosedterm", RETRIEVAL.render_text(packet))
        self.assertNotIn("author-only guidance", json.dumps(packet))

    def test_json_cli_works_outside_vault_and_emits_compact_candidate_fields(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "AI Safety",
                    "--limit",
                    "1",
                    "--json",
                    "--vault",
                    str(FIXTURE_VAULT),
                ],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )

        packet = json.loads(completed.stdout)
        candidate = packet["candidates"][0]
        self.assertEqual(candidate["file"], "Knowledge/AI Safety.md")
        self.assertEqual(candidate["kind"], "concept")
        self.assertEqual(candidate["created"], "2026-08-11")
        self.assertNotIn("aliases", candidate)
        self.assertNotIn("Long evidence", completed.stdout)

    def test_limit_has_no_fixed_maximum_but_must_be_positive(self) -> None:
        self.assertEqual(RETRIEVAL.result_limit("100"), 100)
        with self.assertRaisesRegex(RETRIEVAL.argparse.ArgumentTypeError, "at least 1"):
            RETRIEVAL.result_limit("0")


if __name__ == "__main__":
    unittest.main()
