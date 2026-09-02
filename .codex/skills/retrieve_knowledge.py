#!/usr/bin/env python3
"""Return a deterministic hybrid shortlist of candidate Knowledge notes."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import TextIO


VAULT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    VAULT
    / ".codex"
    / "skills"
    / "second-brain-librarian"
    / "scripts"
    / "validate_taxonomy.py"
)
DEFAULT_LIMIT = 4
MAX_FRONTMATTER_LINES = 100
MAX_SCAN_LINES = 500
MAX_SUMMARY_CHARS = 720
WORD_RE = re.compile(r"[^\W_]+(?:[-'’][^\W_]+)*", re.UNICODE)
STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "what",
    "when",
    "where",
    "which",
    "with",
}


def _load_validator():
    spec = importlib.util.spec_from_file_location("second_brain_taxonomy", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load taxonomy parser from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def normalized(value: str) -> str:
    return " ".join(word.casefold() for word in WORD_RE.findall(value))


def meaningful_terms(value: str) -> list[str]:
    terms = [word for word in normalized(value).split() if word not in STOP_WORDS]
    return list(dict.fromkeys(terms or normalized(value).split()))


def term_variants(term: str) -> set[str]:
    """Return a few conservative morphology variants for common concept nouns."""
    variants = {term}
    if len(term) > 5 and term.endswith("ism"):
        stem = term[:-3]
        variants.update({f"{stem}ist", f"{stem}istic"})
    elif len(term) > 5 and term.endswith("ist"):
        stem = term[:-3]
        variants.add(f"{stem}ism")
    elif len(term) > 7 and term.endswith("istic"):
        stem = term[:-5]
        variants.update({f"{stem}ism", f"{stem}ist"})
    return variants


def without_html_comments(text: str) -> str:
    """Remove HTML comments without joining visible text around them."""
    visible_parts: list[str] = []
    cursor = 0
    while True:
        opener = text.find("<!--", cursor)
        if opener == -1:
            visible_parts.append(text[cursor:])
            break

        visible_parts.append(text[cursor:opener])
        closer = text.find("-->", opener + 4)
        comment_end = len(text) if closer == -1 else closer + 3
        comment = text[opener:comment_end]
        visible_parts.append(" " + "\n" * comment.count("\n"))
        cursor = comment_end

        if closer == -1:
            break

    return "".join(visible_parts)


def _read_frontmatter(handle: TextIO, path: Path) -> dict[str, object]:
    first = handle.readline()
    if first.rstrip("\r\n") != "---":
        raise VALIDATOR.FrontmatterError("missing opening frontmatter delimiter")

    lines = [first]
    for line_number in range(2, MAX_FRONTMATTER_LINES + 1):
        line = handle.readline()
        if not line:
            break
        lines.append(line)
        if line.rstrip("\r\n") == "---":
            return VALIDATOR.parse_frontmatter("".join(lines), path.stem)
    raise VALIDATOR.FrontmatterError(
        f"missing closing frontmatter delimiter within {MAX_FRONTMATTER_LINES} lines"
    )


def _read_title_and_summary(handle: TextIO, fallback_title: str) -> tuple[str, str]:
    title = fallback_title
    summary_parts: list[str] = []
    in_summary = False
    scanned_text = "".join(line for _, line in zip(range(MAX_SCAN_LINES), handle))

    for line in without_html_comments(scanned_text).splitlines():
        stripped = line.strip()
        if stripped.startswith("# ") and not in_summary:
            title = stripped[2:].strip() or title
        if stripped == "## Summary":
            in_summary = True
            continue
        if in_summary and stripped.startswith("## "):
            break
        if in_summary and stripped:
            summary_parts.append(stripped)
            if sum(len(part) for part in summary_parts) >= MAX_SUMMARY_CHARS:
                break

    summary = " ".join(summary_parts)
    if len(summary) > MAX_SUMMARY_CHARS:
        summary = summary[: MAX_SUMMARY_CHARS - 1].rstrip() + "…"
    return title, summary


def read_note(path: Path, vault: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        metadata = _read_frontmatter(handle, path)
        title, summary = _read_title_and_summary(handle, path.stem)
    text = path.read_text(encoding="utf-8")
    visible_body = without_html_comments(
        VALIDATOR.without_code(VALIDATOR.note_body(text))
    )

    aliases = metadata.get("aliases", [])
    if not isinstance(aliases, list):
        aliases = []
    domains = metadata.get("domains", [])
    if not isinstance(domains, list):
        domains = []

    return {
        "_metadata": metadata,
        "file": path.relative_to(vault).as_posix(),
        "title": title,
        "aliases": aliases,
        "kind": metadata.get("kind"),
        "source_type": metadata.get("source_type"),
        "domains": domains,
        "map_for": metadata.get("map_for"),
        "stance": metadata.get("stance"),
        "created": metadata.get("created"),
        "source_checked": metadata.get("source_checked"),
        "summary": summary,
        "_body": visible_body,
    }


def _matching_terms(query_terms: list[str], value: str) -> list[str]:
    value_terms = set(meaningful_terms(value))
    return [
        term
        for term in query_terms
        if term_variants(term).intersection(value_terms)
    ]


def score_note(
    note: dict[str, object], query: str, registry: dict[str, dict[str, object]]
) -> tuple[int, list[str]]:
    query_normalized = normalized(query)
    query_terms = meaningful_terms(query)
    title = str(note["title"])
    title_normalized = normalized(title)
    aliases = [alias for alias in note.get("aliases", []) if isinstance(alias, str)]
    distinct_aliases = [
        alias for alias in aliases if normalized(alias) != title_normalized
    ]

    if query_normalized == title_normalized:
        return 1000, ["exact title"]
    if query_normalized and any(query_normalized == normalized(alias) for alias in aliases):
        return 950, ["exact alias"]

    score = 0
    rationale: list[str] = []
    title_hits = _matching_terms(query_terms, title)
    alias_hits = _matching_terms(query_terms, " ".join(distinct_aliases))
    summary_hits = _matching_terms(query_terms, str(note.get("summary") or ""))
    visible_body = str(note.get("_body") or "")
    body_hits = _matching_terms(query_terms, visible_body)

    if query_normalized and query_normalized in title_normalized:
        score += 320
        rationale.append("title phrase")
    elif title_hits:
        score += 100 * len(title_hits)
        rationale.append(f"title: {', '.join(title_hits)}")

    alias_text = " ".join(normalized(alias) for alias in distinct_aliases)
    if query_normalized and query_normalized in alias_text:
        score += 280
        rationale.append("alias phrase")
    elif alias_hits:
        score += 85 * len(alias_hits)
        rationale.append(f"aliases: {', '.join(alias_hits)}")

    if summary_hits:
        unmatched_summary_hits = [
            term for term in summary_hits if term not in title_hits and term not in alias_hits
        ]
        score += 28 * len(unmatched_summary_hits)
        rationale.append(f"summary: {', '.join(summary_hits)}")

    domain_hits: list[str] = []
    exact_domain = False
    for domain in note.get("domains", []):
        if not isinstance(domain, str) or domain not in registry:
            continue
        entry = registry[domain]
        domain_text = " ".join(
            [
                domain,
                str(entry["description"]),
                *[str(item) for item in entry["includes"]],
                str(entry["hub_note"]),
            ]
        )
        hits = _matching_terms(query_terms, domain_text)
        domain_hits.extend(term for term in hits if term not in domain_hits)
        exact_domain = exact_domain or query_normalized == normalized(domain)
    if exact_domain:
        score += 90
        rationale.append("exact domain")
    if domain_hits:
        unmatched_domain_hits = [
            term
            for term in domain_hits
            if term not in title_hits
            and term not in alias_hits
            and term not in summary_hits
        ]
        score += 12 * len(unmatched_domain_hits)
        rationale.append(f"domains: {', '.join(domain_hits)}")

    structured_text = " ".join(
        [title, *aliases, str(note.get("summary") or "")]
    )
    if (
        query_normalized
        and len(query_terms) > 1
        and query_normalized in normalized(visible_body)
        and query_normalized not in normalized(structured_text)
    ):
        score += 140
        rationale.append("body phrase")
    unmatched_body_hits = [
        term
        for term in body_hits
        if term not in title_hits
        and term not in alias_hits
        and term not in summary_hits
        and term not in domain_hits
    ]
    if unmatched_body_hits:
        score += 10 * len(unmatched_body_hits)
        rationale.append(f"body: {', '.join(unmatched_body_hits)}")

    structured_terms = set(title_hits + alias_hits + summary_hits + domain_hits)
    body_only_terms = set(body_hits) - structured_terms
    score += 45 * max(0, len(structured_terms) - 1)
    score += 20 * max(0, len(body_only_terms) - 1)
    if note.get("map_for") is not None:
        score -= 25
        rationale.append("domain guide orientation -25")

    return min(score, 899), rationale


def _map_routing(
    note: dict[str, object], registry: dict[str, dict[str, object]]
) -> list[dict[str, str]]:
    routes: list[dict[str, str]] = []
    for domain in note.get("domains", []):
        if isinstance(domain, str) and domain in registry:
            routes.append(
                {
                    "domain": domain,
                    "hub_note": str(registry[domain]["hub_note"]),
                }
            )
    return routes


def retrieve(vault: Path, query: str, limit: int = DEFAULT_LIMIT) -> dict[str, object]:
    vault = vault.resolve()
    registry_path = vault / ".codex" / "skills" / "knowledge-domains.json"
    registry = VALIDATOR.load_registry(registry_path)
    knowledge = vault / "Knowledge"
    if not knowledge.is_dir():
        raise OSError(f"Knowledge directory not found: {knowledge}")
    candidates: list[dict[str, object]] = []
    warnings: list[dict[str, str]] = []

    for path in sorted(knowledge.glob("*.md"), key=lambda item: item.name.casefold()):
        if path.name == "Knowledge.md":
            continue
        try:
            note = read_note(path, vault)
        except (OSError, UnicodeError, VALIDATOR.FrontmatterError) as error:
            warnings.append(
                {
                    "file": path.relative_to(vault).as_posix(),
                    "reason": str(error),
                }
            )
            continue
        metadata_errors = VALIDATOR.validate_metadata(
            note.pop("_metadata"), set(registry)
        )
        if metadata_errors:
            warnings.append(
                {
                    "file": path.relative_to(vault).as_posix(),
                    "reason": "; ".join(metadata_errors),
                }
            )
            continue
        score, rationale = score_note(note, query, registry)
        if score <= 0:
            continue
        note.pop("aliases", None)
        note.pop("_body", None)
        note["map_routing"] = _map_routing(note, registry)
        note["score"] = score
        note["rationale"] = rationale
        candidates.append(note)

    candidates.sort(
        key=lambda note: (
            -int(note["score"]),
            str(note["title"]).casefold(),
            str(note["file"]).casefold(),
        )
    )
    return {
        "query": query,
        "limit": limit,
        "candidates": candidates[:limit],
        "warnings": warnings,
    }


def _optional(value: object) -> str:
    return str(value) if value not in (None, "", []) else "—"


def render_text(packet: dict[str, object]) -> str:
    candidates = packet["candidates"]
    lines = [
        f"Query: {packet['query']}",
        f"Candidates: {len(candidates)} (limit {packet['limit']})",
    ]
    for index, note in enumerate(candidates, start=1):
        source_type = (
            f"/{note['source_type']}" if note.get("source_type") is not None else ""
        )
        routes = "; ".join(
            f"{route['domain']} -> [[{route['hub_note']}]]"
            for route in note["map_routing"]
        ) or "—"
        freshness = f"created {_optional(note.get('created'))}"
        if note.get("source_checked") is not None:
            freshness += f"; source_checked {note['source_checked']}"
        lines.extend(
            [
                "",
                f"{index}. {note['title']} — {note['file']}",
                f"   score {note['score']}: {'; '.join(note['rationale'])}",
                f"   kind: {_optional(note.get('kind'))}{source_type}; stance: {_optional(note.get('stance'))}",
                f"   routing: {routes}",
                f"   freshness: {freshness}",
                f"   summary: {_optional(note.get('summary'))}",
            ]
        )
    if packet["warnings"]:
        lines.extend(["", f"Warnings: {len(packet['warnings'])} malformed/unreadable note(s) skipped."])
        lines.extend(
            f"- {warning['file']}: {warning['reason']}" for warning in packet["warnings"]
        )
    return "\n".join(lines)


def result_limit(value: str) -> int:
    limit = int(value)
    if limit < 1:
        raise argparse.ArgumentTypeError("limit must be at least 1")
    return limit


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select a ranked shortlist of Knowledge-note candidates."
    )
    parser.add_argument("query", help="title, alias, concept, or domain query")
    parser.add_argument(
        "-n", "--limit", type=result_limit, default=DEFAULT_LIMIT, help="result count (default: 4; no fixed maximum)"
    )
    parser.add_argument("--json", action="store_true", help="emit deterministic JSON")
    parser.add_argument(
        "--vault",
        type=Path,
        default=VAULT,
        help=argparse.SUPPRESS,
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        packet = retrieve(args.vault, args.query, args.limit)
    except (OSError, VALIDATOR.RegistryError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(packet, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(packet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
