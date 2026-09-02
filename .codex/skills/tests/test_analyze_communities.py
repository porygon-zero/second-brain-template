#!/usr/bin/env python3
"""Focused tests for community-domain analysis."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path


SKILLS = Path(__file__).resolve().parents[1]
SCRIPT = SKILLS / "analyze_communities.py"
SPEC = importlib.util.spec_from_file_location("analyze_communities", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ANALYZER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ANALYZER)


class CommunityAnalysisTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.vault = Path(self.directory.name)
        (self.vault / "Knowledge").mkdir()
        (self.vault / ".obsidian").mkdir()
        (self.vault / ".codex" / "skills").mkdir(parents=True)
        registry = {
            "alpha": {
                "hub_note": "Alpha Map",
                "description": "Alpha material.",
                "includes": ["alpha"],
                "excludes": ["beta"],
            }
        }
        (self.vault / ".codex" / "skills" / "knowledge-domains.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )
        (self.vault / ".obsidian" / "graph.json").write_text(
            json.dumps(
                {
                    "search": "keep me",
                    "colorGroups": [{"query": "old", "color": {"a": 1, "rgb": 1}}],
                    "scale": 0.42,
                },
                indent=2,
            ),
            encoding="utf-8",
        )

        self._note("A One", ["A Two", "A Three"], aliases=["Alpha Root"])
        self._note("A Two", ["Alpha Root", "A Three"])
        self._note("A Three", ["A One", "A Two", "B One"])
        self._note("B One", ["B Two", "B Three", "A Three"])
        self._note("B Two", ["B One", "B Three"])
        self._note("B Three", ["B One", "B Two"])
        self._note(
            "Alpha Map",
            ["A One", "A Two", "A Three", "B One", "B Two", "B Three"],
            map_for="alpha",
        )
        self._note("Knowledge", ["Alpha Map", "A One", "B One"])

    def tearDown(self) -> None:
        self.directory.cleanup()

    def _note(
        self,
        title: str,
        links: list[str],
        aliases: list[str] | None = None,
        map_for: str | None = None,
    ) -> None:
        alias_text = ""
        if aliases:
            alias_text = "aliases:\n" + "".join(f"  - {alias}\n" for alias in aliases)
        map_text = f"map_for: {map_for}\n" if map_for else ""
        body_links = "\n".join(f"- [[{link}]]" for link in links)
        text = (
            "---\n"
            "type: knowledge\n"
            f"kind: {'synthesis' if map_for else 'concept'}\n"
            "stance: reference\n"
            f"{map_text}"
            "domains:\n"
            "  - alpha\n"
            f"{alias_text}"
            "created: 2026-08-18\n"
            "---\n\n"
            f"# {title}\n\n"
            "## Summary\n\n"
            f"{title} summary.\n\n"
            "## Relationships\n\n"
            f"{body_links}\n"
        )
        (self.vault / "Knowledge" / f"{title}.md").write_text(text, encoding="utf-8")

    def test_navigation_hubs_are_excluded_and_alias_links_resolve(self) -> None:
        report = ANALYZER.analyze(self.vault)

        self.assertEqual(report["graph"]["nodes"], 6)
        self.assertEqual(report["graph"]["edges"], 7)
        self.assertFalse(report["graph"]["navigation_included"])
        self.assertEqual(sorted(row["size"] for row in report["communities"]), [3, 3])
        self.assertEqual(report["warnings"], [])

        with_navigation = ANALYZER.analyze(self.vault, include_navigation=True)
        self.assertEqual(with_navigation["graph"]["nodes"], 8)
        self.assertTrue(with_navigation["graph"]["navigation_included"])
        self.assertEqual(with_navigation["warnings"], [])

    def test_domain_fragmentation_is_a_review_signal_not_a_proposal(self) -> None:
        report = ANALYZER.analyze(self.vault)
        alpha = next(row for row in report["domains"] if row["domain"] == "alpha")

        self.assertEqual(alpha["community_count"], 2)
        self.assertEqual(alpha["dominant_share"], 0.5)
        self.assertTrue(
            any(
                signal["signal"] == "domain-fragmentation"
                for signal in report["review_signals"]
            )
        )
        self.assertEqual(
            report["authority"]["review_signals"],
            "candidates for human review, not domain proposals",
        )

    def test_json_cli_is_deterministic_and_does_not_change_the_registry(self) -> None:
        registry = self.vault / ".codex" / "skills" / "knowledge-domains.json"
        before = registry.read_bytes()
        command = [
            sys.executable,
            str(SCRIPT),
            "--vault",
            str(self.vault),
            "--json",
        ]
        first = subprocess.run(command, check=True, capture_output=True, text=True)
        second = subprocess.run(command, check=True, capture_output=True, text=True)

        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(registry.read_bytes(), before)
        self.assertEqual(json.loads(first.stdout)["schema_version"], 1)

    def test_publish_writes_dated_note_and_only_replaces_graph_colors(self) -> None:
        report = ANALYZER.analyze(self.vault)
        graph_path = self.vault / ".obsidian" / "graph.json"
        before = json.loads(graph_path.read_text(encoding="utf-8"))

        report_path, published_graph = ANALYZER.publish(
            report, self.vault, date(2026, 8, 18)
        )

        self.assertEqual(report_path, self.vault.resolve() / ANALYZER.LATEST_REPORT)
        self.assertEqual(published_graph, graph_path.resolve())
        note = report_path.read_text(encoding="utf-8")
        self.assertIn("analyzed: 2026-08-18", note)
        self.assertIn("### C01 - 3 notes", note)
        self.assertIn("Graph color: `#", note)
        self.assertIn("[[A One]]", note)

        after = json.loads(graph_path.read_text(encoding="utf-8"))
        self.assertEqual(after["search"], before["search"])
        self.assertEqual(after["scale"], before["scale"])
        self.assertNotEqual(after["colorGroups"], before["colorGroups"])
        self.assertEqual(len(after["colorGroups"]), len(report["communities"]) + 1)
        self.assertTrue(after["colorGroups"][0]["query"].startswith('path:"Knowledge/'))
        self.assertEqual(after["colorGroups"][-1]["query"], 'path:"Knowledge"')


if __name__ == "__main__":
    unittest.main()
