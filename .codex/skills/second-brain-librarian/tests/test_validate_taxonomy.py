"""Focused tests for the knowledge taxonomy validator."""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_taxonomy.py"
SPEC = importlib.util.spec_from_file_location("validate_taxonomy", SCRIPT)
assert SPEC and SPEC.loader
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def metadata(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "type": "knowledge",
        "kind": "concept",
        "created": "2026-08-10",
        "domains": ["software-development"],
    }
    values.update(overrides)
    return values


class FrontmatterTests(unittest.TestCase):
    def test_parses_block_and_inline_arrays(self) -> None:
        parsed = validator.parse_frontmatter(
            """---
type: knowledge
kind: concept
created: 2026-08-10
domains: [software-development, "software-architecture"]
aliases:
  - ADR
  - 'Decision record'
---
# Note
"""
        )
        self.assertEqual(parsed["domains"], ["software-development", "software-architecture"])
        self.assertEqual(parsed["aliases"], ["ADR", "Decision record"])

    def test_rejects_malformed_inline_array(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "malformed inline list"):
            validator.parse_frontmatter("---\ndomains: [software-development\n---\n")

    def test_reports_missing_closing_delimiter_before_note_content(self) -> None:
        with self.assertRaisesRegex(validator.FrontmatterError, "closing frontmatter delimiter"):
            validator.parse_frontmatter("---\ntype: knowledge\n# note\n", "note")


class CompletedNoteTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.vault = Path(directory.name)
        (self.vault / "Knowledge").mkdir()
        (self.vault / "Templates").mkdir()

    def write_note(
        self,
        relative: str,
        *,
        title: str | None = None,
        aliases: tuple[str, ...] = (),
        body: str = "",
    ) -> Path:
        path = self.vault / relative
        alias_lines = ""
        if aliases:
            alias_lines = "aliases:\n" + "".join(f"  - {alias}\n" for alias in aliases)
        heading = f"# {title}\n\n" if title is not None else ""
        path.write_text(
            "---\n"
            "type: knowledge\n"
            "kind: concept\n"
            "created: 2026-08-10\n"
            "domains: [software-development]\n"
            f"{alias_lines}"
            "---\n\n"
            f"{heading}"
            "## Summary\n\nSummary.\n\n"
            f"{body}\n\n"
            "## Sources\n\n- Source.\n",
            encoding="utf-8",
        )
        return path

    def errors(self, path: Path) -> list[str]:
        return validator.validate_completed_note(
            path,
            validator.frontmatter(path),
            validator.build_link_index(self.vault),
        )

    def test_accepts_aliases_display_text_paths_fragments_and_ignores_code(self) -> None:
        self.write_note("Knowledge/Target.md", title="Target", aliases=("Target Alias",))
        self.write_note("Templates/Guide.md", title="Guide")
        (self.vault / "Knowledge" / "Navigation.base").write_text("views: []\n", encoding="utf-8")
        source = self.write_note(
            "Knowledge/Source.md",
            title="Source",
            body="""[[Target Alias|display text]]
[[Knowledge/Target#Details]]
[[Templates/Guide#Usage|guide]]
[[Knowledge/Navigation.base|navigation]]
[[Target#^block-id]]
[[#Summary]]

`[[Missing Inline Code]]`

```markdown
# Not the note title
[[Missing Fenced Code]]
<kind>
```""",
        )
        self.assertEqual(self.errors(source), [])

    def test_ignores_wikilinks_inside_matching_multi_backtick_spans(self) -> None:
        cases = (
            "`` `foo` [[Missing Double Span]] ``",
            "``` ``foo`` [[Missing Triple Span]] ```",
        )
        for index, body in enumerate(cases):
            with self.subTest(body=body):
                source = self.write_note(
                    f"Knowledge/Multi Span {index}.md",
                    title=f"Multi Span {index}",
                    body=body,
                )
                self.assertEqual(self.errors(source), [])

    def test_ignores_wikilinks_inside_single_backtick_spans(self) -> None:
        source = self.write_note(
            "Knowledge/Single Span.md",
            title="Single Span",
            body="`[[Missing Single Span]]`",
        )
        self.assertEqual(self.errors(source), [])

    def test_unmatched_backticks_do_not_hide_wikilinks(self) -> None:
        source = self.write_note(
            "Knowledge/Unmatched Span.md",
            title="Unmatched Span",
            body="`` [[Missing After Unmatched Backticks]]",
        )
        self.assertIn(
            "unresolved wikilink 'Missing After Unmatched Backticks'",
            self.errors(source),
        )

    def test_validates_real_wikilinks_outside_multi_backtick_spans(self) -> None:
        source = self.write_note(
            "Knowledge/Outside Span.md",
            title="Outside Span",
            body=(
                "`` `foo` [[Missing Inside Code]] ``\n"
                "[[Missing Outside Code]]"
            ),
        )
        errors = self.errors(source)
        self.assertNotIn("unresolved wikilink 'Missing Inside Code'", errors)
        self.assertIn("unresolved wikilink 'Missing Outside Code'", errors)

    def test_distinguishes_broken_and_ambiguous_wikilinks(self) -> None:
        self.write_note("Knowledge/One.md", title="One", aliases=("Shared",))
        self.write_note("Knowledge/Two.md", title="Two", aliases=("Shared",))
        source = self.write_note(
            "Knowledge/Source.md",
            title="Source",
            body="[[Missing]]\n[[Shared]]",
        )
        errors = self.errors(source)
        self.assertIn("unresolved wikilink 'Missing'", errors)
        self.assertIn("ambiguous wikilink 'Shared'", errors)

    def test_requires_first_h1_to_match_filename_or_alias(self) -> None:
        missing = self.write_note("Knowledge/Missing Heading.md")
        mismatch = self.write_note("Knowledge/Canonical.md", title="Different")
        aliased = self.write_note(
            "Knowledge/Aliased.md", title="Intentional Title", aliases=("Intentional Title",)
        )
        self.assertIn("missing required first H1", self.errors(missing))
        self.assertTrue(any("must match the filename" in error for error in self.errors(mismatch)))
        self.assertEqual(self.errors(aliased), [])

    def test_requires_summary_and_sources(self) -> None:
        path = self.write_note("Knowledge/Incomplete.md", title="Incomplete")
        path.write_text(
            path.read_text(encoding="utf-8")
            .replace("## Summary", "## Overview")
            .replace("## Sources", "## References"),
            encoding="utf-8",
        )
        errors = self.errors(path)
        self.assertIn("missing required '## Summary' section", errors)
        self.assertIn("missing required '## Sources' section", errors)

    def test_rejects_unresolved_template_sentinel_outside_templates(self) -> None:
        path = self.write_note(
            "Knowledge/Sentinel.md",
            title="Sentinel",
            body="<!-- Replace <domain> before saving. -->\n{{title}}",
        )
        errors = self.errors(path)
        self.assertIn("unresolved template sentinel '<domain>'", errors)
        self.assertIn("unresolved template sentinel '{{title}}'", errors)


class MetadataTests(unittest.TestCase):
    DOMAINS = {"software-development", "software-architecture", "artificial-intelligence", "power-systems"}

    def errors(self, *, as_of: date | None = None, **overrides: object) -> list[str]:
        return validator.validate_metadata(
            metadata(**overrides), self.DOMAINS, as_of=as_of
        )

    def test_requires_domains(self) -> None:
        values = metadata()
        del values["domains"]
        self.assertIn("missing required domains", validator.validate_metadata(values, self.DOMAINS))

    def test_rejects_malformed_domains(self) -> None:
        self.assertIn("domains must be a list", self.errors(domains="software-development"))
        self.assertIn("domains must be a nonempty list", self.errors(domains=[]))

    def test_rejects_unknown_duplicate_and_excessive_domains(self) -> None:
        self.assertTrue(any("unknown domains: unknown" in error for error in self.errors(domains=["unknown"])))
        self.assertIn(
            "domains must not contain duplicates",
            self.errors(domains=["software-development", "software-development"]),
        )
        self.assertIn(
            "domains must contain between 1 and 3 values",
            self.errors(domains=list(self.DOMAINS)),
        )

    def test_rejects_malformed_aliases(self) -> None:
        self.assertIn("aliases must be a list", self.errors(aliases="ADR"))
        self.assertIn("aliases must be a nonempty list", self.errors(aliases=[]))
        self.assertIn("aliases must contain only nonempty strings", self.errors(aliases=[""]))
        self.assertIn("aliases must not contain duplicates", self.errors(aliases=["ADR", "ADR"]))

    def test_requires_type_and_created(self) -> None:
        values = metadata()
        del values["type"]
        del values["created"]
        errors = validator.validate_metadata(values, self.DOMAINS)
        self.assertIn("type must be 'knowledge'", errors)
        self.assertIn("created must be an ISO date (YYYY-MM-DD)", errors)
        self.assertIn("created must be an ISO date (YYYY-MM-DD)", self.errors(created="2026-02-30"))

    def test_preserves_stance_and_source_rules(self) -> None:
        errors = self.errors(stance="certain", source_checked="yesterday", source_type="book")
        self.assertIn("unsupported stance 'certain'", errors)
        self.assertIn("source_checked must be an ISO date (YYYY-MM-DD)", errors)
        self.assertIn("source_type is only valid with kind 'source'", errors)
        self.assertIn("kind 'source' requires source_type", self.errors(kind="source"))
        self.assertIn("kind 'source' requires source_type", self.errors(kind="source", source_type=""))

    def test_accepts_each_canonical_source_type(self) -> None:
        for source_type in validator.SOURCE_TYPE_SECTIONS:
            with self.subTest(source_type=source_type):
                self.assertEqual(
                    self.errors(kind="source", source_type=source_type), []
                )

    def test_rejects_source_type_typos_case_variants_and_unknown_values(self) -> None:
        for source_type in ("bok", "Book", "video"):
            with self.subTest(source_type=source_type):
                self.assertTrue(
                    any(
                        f"unsupported source_type '{source_type}'" in error
                        for error in self.errors(kind="source", source_type=source_type)
                    )
                )

    def test_rejects_non_scalar_source_type_without_crashing(self) -> None:
        self.assertIn(
            "kind 'source' requires source_type",
            self.errors(kind="source", source_type=["book"]),
        )

    def test_accepts_absent_current_and_past_source_checked_dates(self) -> None:
        as_of = date(2026, 8, 11)
        self.assertEqual(self.errors(as_of=as_of), [])
        self.assertEqual(self.errors(as_of=as_of, source_checked="2026-08-11"), [])
        self.assertEqual(self.errors(as_of=as_of, source_checked="2026-08-10"), [])

    def test_rejects_future_source_checked_date_against_injected_date(self) -> None:
        self.assertIn(
            "source_checked must not be in the future",
            self.errors(
                as_of=date(2026, 8, 11), source_checked="2026-08-12"
            ),
        )

    def test_accepts_perspective_as_first_class_knowledge(self) -> None:
        self.assertEqual(self.errors(kind="perspective", stance="exploring"), [])

    def test_rejects_unresolved_knowledge_sentinels(self) -> None:
        errors = self.errors(kind="<kind>", domains=["<domain>"])
        self.assertTrue(any("unsupported or missing kind" in error for error in errors))
        self.assertIn("unknown domains: <domain>", errors)


class ArtifactTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.vault = Path(directory.name)
        (self.vault / "Knowledge").mkdir()
        (self.vault / "Reviews").mkdir()
        (self.vault / "Decisions").mkdir()
        (self.vault / "Knowledge" / "Evidence.md").write_text(
            "# Evidence\n", encoding="utf-8"
        )

    def validate(self, relative: str, artifact_type: str, text: str) -> list[str]:
        path = self.vault / relative
        path.write_text(text, encoding="utf-8")
        return validator.validate_completed_artifact(
            path, artifact_type, validator.build_link_index(self.vault)
        )

    def test_accepts_completed_review(self) -> None:
        errors = self.validate(
            "Reviews/Review.md",
            "review",
            """---
type: review
review_type: knowledge
date: 2026-08-13
---
# Knowledge Review - 2026-08-13

Used [[Evidence]].
""",
        )
        self.assertEqual(errors, [])

    def test_rejects_malformed_review(self) -> None:
        errors = self.validate(
            "Reviews/Review.md",
            "review",
            """---
type: knowledge
review_type: vault
date: tomorrow
---
No heading. [[Missing]]. {{title}}
""",
        )
        self.assertIn("type must be 'review'", errors)
        self.assertIn("review_type must be 'knowledge'", errors)
        self.assertIn("date must be an ISO date (YYYY-MM-DD)", errors)
        self.assertIn("missing required first H1", errors)
        self.assertIn("unresolved template sentinel '{{title}}'", errors)
        self.assertIn("unresolved wikilink 'Missing'", errors)

    def test_accepts_completed_decision_record(self) -> None:
        errors = self.validate(
            "Decisions/Decision.md",
            "decision-record",
            """---
type: decision-record
status: accepted
author: Maintainer
created: 2026-08-13
---
# ADR - Decision

Supported by [[Evidence]].
""",
        )
        self.assertEqual(errors, [])

    def test_rejects_malformed_decision_record(self) -> None:
        errors = self.validate(
            "Decisions/Decision.md",
            "decision-record",
            """---
type: decision-record
status: complete
author:
created: 2026-02-30
---
# ADR - Decision
""",
        )
        self.assertTrue(any("status must be one of" in error for error in errors))
        self.assertIn("author must be a nonempty string", errors)
        self.assertIn("created must be an ISO date (YYYY-MM-DD)", errors)


class MapMetadataTests(unittest.TestCase):
    REGISTRY = {
        "software": {"hub_note": "Software Map"},
        "energy": {"hub_note": "Energy Map"},
    }

    def test_configured_hub_requires_synthesis_matching_map_and_single_domain(self) -> None:
        errors = validator.validate_map_metadata(
            "Software Map",
            metadata(kind="concept", map_for="energy", domains=["software", "energy"]),
            self.REGISTRY,
        )
        self.assertTrue(any("kind 'synthesis'" in error for error in errors))
        self.assertTrue(any("map_for must be 'software'" in error for error in errors))
        self.assertTrue(any("domains must be exactly ['software']" in error for error in errors))

    def test_rejects_map_for_on_unregistered_or_nonhub_note(self) -> None:
        unknown = validator.validate_map_metadata(
            "Other", metadata(map_for="unknown"), self.REGISTRY
        )
        reserved = validator.validate_map_metadata(
            "Other", metadata(map_for="software"), self.REGISTRY
        )
        self.assertTrue(any("unregistered domain 'unknown'" in error for error in unknown))
        self.assertTrue(any("reserved for configured hub 'Software Map'" in error for error in reserved))


class RegistryTests(unittest.TestCase):
    def write_registry(self, value: object) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = Path(directory.name) / "domains.json"
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def test_loads_valid_registry(self) -> None:
        path = self.write_registry(
            {"software": {"hub_note": "Software Map", "description": "Software.", "includes": [], "excludes": []}}
        )
        self.assertIn("software", validator.load_registry(path))

    def test_rejects_malformed_registry(self) -> None:
        malformed_values = [
            {},
            {"software": []},
            {"software": {"hub_note": "", "description": "Software.", "includes": [], "excludes": []}},
            {"software": {"hub_note": "Map", "description": "Software.", "includes": "code", "excludes": []}},
        ]
        for value in malformed_values:
            with self.subTest(value=value), self.assertRaises(validator.RegistryError):
                validator.load_registry(self.write_registry(value))

    def test_rejects_duplicate_registry_hubs(self) -> None:
        entry = {"hub_note": "Shared Map", "description": "Scope.", "includes": [], "excludes": []}
        with self.assertRaisesRegex(validator.RegistryError, "assigned to both"):
            validator.load_registry(self.write_registry({"software": entry, "energy": entry}))


class DomainGuideTests(unittest.TestCase):
    def test_requires_each_configured_guide_note(self) -> None:
        registry = {
            "software": {"hub_note": "Software Map"},
            "energy": {"hub_note": "Energy Map"},
        }
        errors = validator.validate_hubs(registry, {"Software Map"})
        self.assertFalse(any("Software Map" in error for error in errors))
        self.assertTrue(any("Energy Map.md" in error and "missing" in error for error in errors))


class PerspectiveIdentityTests(unittest.TestCase):
    def test_accepts_only_the_canonical_perspective(self) -> None:
        notes = {"Second Brain Perspective", "Concept"}
        metadata_by_note = {
            "Second Brain Perspective": metadata(kind="perspective"),
            "Concept": metadata(),
        }
        self.assertEqual(
            validator.validate_perspective_identity(notes, metadata_by_note), []
        )

    def test_rejects_missing_or_additional_perspective(self) -> None:
        errors = validator.validate_perspective_identity(
            {"Alternative Perspective"},
            {"Alternative Perspective": metadata(kind="perspective")},
        )
        self.assertTrue(any("required perspective note is missing" in error for error in errors))
        self.assertTrue(any("kind 'perspective' is reserved" in error for error in errors))

    def test_requires_canonical_note_to_be_a_perspective(self) -> None:
        errors = validator.validate_perspective_identity(
            {"Second Brain Perspective"},
            {"Second Brain Perspective": metadata(kind="synthesis")},
        )
        self.assertIn(
            "Knowledge/Second Brain Perspective.md: kind must be 'perspective'", errors
        )


class TemplateContractTests(unittest.TestCase):
    def write_templates(self, overrides: dict[str, str] | None = None) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        templates = Path(directory.name)
        files = {
            "Concept definition.md": """---
type: knowledge
kind: concept
domains: [<domain>]
created: "{{date:YYYY-MM-DD}}"
---
<!-- Replace every unresolved sentinel: <domain>. -->
# {{title}}
""",
            "Knowledge note.md": """---
type: knowledge
kind: <kind>
domains: [<domain>]
created: "{{date:YYYY-MM-DD}}"
---
<!-- Replace every unresolved sentinel: <kind> and <domain>. -->
# {{title}}
""",
            "Domain map.md": """---
type: knowledge
kind: synthesis
map_for: <domain>
domains: [<domain>]
created: "{{date:YYYY-MM-DD}}"
---
<!-- Replace every unresolved sentinel: <domain>. -->
# {{title}}
""",
            "Knowledge review.md": """---
type: review
review_type: knowledge
date: "{{date:YYYY-MM-DD}}"
---
# Knowledge Review - {{date:YYYY-MM-DD}}
<!-- Which notes informed a decision, explanation, conversation, or creation? -->
""",
            "Architecture Decision Record.md": """---
type: decision-record
status: <status>
author: <author>
created: "{{date:YYYY-MM-DD}}"
---
<!-- Replace every unresolved sentinel: <status>, <author>, and {{title}}. -->
# ADR - {{title}}
""",
        }
        files.update(overrides or {})
        for filename, text in files.items():
            (templates / filename).write_text(text, encoding="utf-8")
        return templates

    def test_accepts_template_sentinels_without_completed_note_validation(self) -> None:
        self.assertEqual(validator.validate_template_contracts(self.write_templates()), [])

    def test_rejects_broken_knowledge_review_contract(self) -> None:
        templates = self.write_templates(
            {
                "Knowledge review.md": """---
type: knowledge
review_type: vault
date: 2026-08-10
---
# Review
"""
            }
        )
        errors = validator.validate_template_contracts(templates)
        review_errors = [error for error in errors if "Knowledge review.md" in error]
        self.assertTrue(any("type must be 'review'" in error for error in review_errors))
        self.assertTrue(any("review_type must be 'knowledge'" in error for error in review_errors))
        self.assertTrue(any("date must be the quoted" in error for error in review_errors))
        self.assertTrue(any("missing required sentinel" in error for error in review_errors))

    def test_rejects_broken_adr_contract(self) -> None:
        templates = self.write_templates(
            {
                "Architecture Decision Record.md": """---
type: knowledge
status: draft
created: 2026-08-10
---
# ADR
"""
            }
        )
        errors = validator.validate_template_contracts(templates)
        adr_errors = [
            error for error in errors if "Architecture Decision Record.md" in error
        ]
        self.assertTrue(any("type must be 'decision-record'" in error for error in adr_errors))
        self.assertTrue(any("status must be '<status>'" in error for error in adr_errors))
        self.assertTrue(any("author must be '<author>'" in error for error in adr_errors))
        self.assertTrue(any("created must be the quoted" in error for error in adr_errors))
        self.assertTrue(any("missing required sentinel" in error for error in adr_errors))


if __name__ == "__main__":
    unittest.main()
