#!/usr/bin/env python3
"""Validate vault artifacts, links, Knowledge taxonomy, and index placement."""

from __future__ import annotations

import ast
import json
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path


VAULT = Path(__file__).resolve().parents[4]
KNOWLEDGE = VAULT / "Knowledge"
REGISTRY = VAULT / ".codex" / "skills" / "knowledge-domains.json"
TEMPLATES = VAULT / "Templates"
REVIEWS = VAULT / "Reviews"
DECISIONS = VAULT / "Decisions"
USER_FACING_DOCUMENTS = (
    VAULT / "Home.md",
    VAULT / "SYSTEM_GUIDE.md",
    VAULT / "VAULT_CONVENTIONS.md",
    VAULT / "Vault Use Log.md",
    KNOWLEDGE / "Knowledge.md",
)

WIKILINK_RE = re.compile(r"\[\[([^]\n]+)\]\]")
H1_RE = re.compile(r"^#\s+(.+?)\s*$", re.MULTILINE)
SUMMARY_RE = re.compile(r"^##\s+Summary\s*$", re.MULTILINE)
SOURCES_RE = re.compile(r"^##\s+Sources\s*$", re.MULTILINE)
TEMPLATE_SENTINEL_RE = re.compile(
    r"\{\{[^{}\n]+\}\}|<(?:kind|domain|status|author)>"
)
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
FENCE_RE = re.compile(r"^[ \t]*(`{3,}|~{3,})(.*)$")
KEY_VALUE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):(?:\s*(.*))?$")
LIST_ITEM_RE = re.compile(r"^[ \t]+-[ \t]+(.*)$")
VALID_STANCES = {"adopted", "aligned", "exploring", "contested", "reference"}
VALID_KINDS = {"concept", "framework", "method", "principle", "source", "perspective", "synthesis"}
VALID_DECISION_STATUSES = {
    "draft",
    "proposed",
    "accepted",
    "adopted",
    "superseded",
    "expired",
}
SOURCE_TYPE_SECTIONS = {
    "book": "Books",
    "article": "Articles, papers, and other sources",
    "paper": "Articles, papers, and other sources",
    "report": "Articles, papers, and other sources",
    "website": "Articles, papers, and other sources",
}
PERSPECTIVE_NOTE = "Second Brain Perspective"


class FrontmatterError(ValueError):
    """Report malformed note frontmatter without crashing validation."""


class RegistryError(ValueError):
    """Report a malformed controlled-domain registry."""


def parse_scalar(value: str, line_number: int) -> str:
    value = value.strip()
    if value.startswith(("'", '"')):
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError) as error:
            raise FrontmatterError(f"malformed quoted scalar on line {line_number}") from error
        if not isinstance(parsed, str):
            raise FrontmatterError(f"scalar on line {line_number} must be a string")
        return parsed
    return value


def parse_inline_list(value: str, line_number: int) -> list[str]:
    if not value.endswith("]"):
        raise FrontmatterError(f"malformed inline list on line {line_number}")
    content = value[1:-1].strip()
    if not content:
        return []

    items: list[str] = []
    start = 0
    quote: str | None = None
    escaped = False
    for offset, character in enumerate(content):
        if escaped:
            escaped = False
        elif character == "\\" and quote == '"':
            escaped = True
        elif character in {"'", '"'}:
            quote = None if quote == character else character if quote is None else quote
        elif character == "," and quote is None:
            items.append(parse_scalar(content[start:offset], line_number))
            start = offset + 1
    if quote is not None:
        raise FrontmatterError(f"unterminated quote in inline list on line {line_number}")
    items.append(parse_scalar(content[start:], line_number))
    return items


def parse_frontmatter(text: str, note_name: str = "note") -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise FrontmatterError("missing opening frontmatter delimiter")

    values: dict[str, object] = {}
    line_index = 1
    while line_index < len(lines):
        line = lines[line_index]
        line_number = line_index + 1
        if line == "---":
            return values
        if not line:
            line_index += 1
            continue
        if line == f"# {note_name}" or line.startswith("## "):
            raise FrontmatterError(
                f"line {line_number} looks like note content; closing frontmatter delimiter may be missing"
            )
        if line.startswith("#"):
            line_index += 1
            continue
        if line.startswith((" ", "\t")):
            raise FrontmatterError(f"unexpected indentation on line {line_number}")
        if line.startswith("-"):
            raise FrontmatterError(f"unexpected top-level list item on line {line_number}")

        match = KEY_VALUE_RE.match(line)
        if not match:
            raise FrontmatterError(
                f"line {line_number} is not a top-level 'key: value' entry; "
                "closing frontmatter delimiter may be missing"
            )
        key, raw_value = match.groups()
        if key in values:
            raise FrontmatterError(f"duplicate frontmatter key '{key}' on line {line_number}")

        raw_value = (raw_value or "").strip()
        if raw_value.startswith("["):
            values[key] = parse_inline_list(raw_value, line_number)
        elif raw_value:
            values[key] = parse_scalar(raw_value, line_number)
        else:
            block_items: list[str] = []
            next_index = line_index + 1
            while next_index < len(lines):
                item_match = LIST_ITEM_RE.match(lines[next_index])
                if not item_match:
                    break
                block_items.append(parse_scalar(item_match.group(1), next_index + 1))
                next_index += 1
            values[key] = block_items if block_items else ""
            line_index = next_index - 1
        line_index += 1
    raise FrontmatterError("missing closing frontmatter delimiter")


def frontmatter(path: Path) -> dict[str, object]:
    return parse_frontmatter(path.read_text(encoding="utf-8"), path.stem)


def note_body(text: str) -> str:
    """Return content after a leading frontmatter block."""
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return text
    for index, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[index + 1 :])
    return text


def without_inline_code(text: str) -> str:
    """Blank matching CommonMark backtick spans without joining visible text."""
    visible = list(text)
    index = 0
    while index < len(text):
        if text[index] != "`":
            index += 1
            continue

        opener_end = index + 1
        while opener_end < len(text) and text[opener_end] == "`":
            opener_end += 1
        delimiter_length = opener_end - index

        search_from = opener_end
        closer_start: int | None = None
        closer_end: int | None = None
        while search_from < len(text):
            candidate_start = text.find("`", search_from)
            if candidate_start == -1:
                break
            candidate_end = candidate_start + 1
            while candidate_end < len(text) and text[candidate_end] == "`":
                candidate_end += 1
            if candidate_end - candidate_start == delimiter_length:
                closer_start = candidate_start
                closer_end = candidate_end
                break
            search_from = candidate_end

        if closer_start is None or closer_end is None:
            index = opener_end
            continue

        for offset in range(index, closer_end):
            if visible[offset] not in {"\n", "\r"}:
                visible[offset] = " "
        index = closer_end

    return "".join(visible)


def without_code(text: str) -> str:
    """Remove fenced and inline code while preserving ordinary Markdown."""
    kept: list[str] = []
    fence_character: str | None = None
    fence_length = 0
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if fence_character is None:
            if match and (match.group(1)[0] == "~" or "`" not in match.group(2)):
                fence_character = match.group(1)[0]
                fence_length = len(match.group(1))
                kept.append("")
                continue
        elif (
            match
            and match.group(1)[0] == fence_character
            and len(match.group(1)) >= fence_length
            and not match.group(2).strip()
        ):
            fence_character = None
            fence_length = 0
            kept.append("")
            continue
        kept.append(line if fence_character is None else "")
    return without_inline_code("\n".join(kept))


def visible_markdown(text: str) -> str:
    """Return body Markdown that can contribute headings or ordinary links."""
    return HTML_COMMENT_RE.sub("", without_code(note_body(text)))


def build_link_index(
    vault: Path = VAULT,
) -> tuple[dict[str, set[Path]], dict[str, set[Path]]]:
    """Index visible vault notes by path, filename, and frontmatter alias."""
    by_path: dict[str, set[Path]] = defaultdict(set)
    by_name: dict[str, set[Path]] = defaultdict(set)
    for path in vault.rglob("*"):
        if not path.is_file() or path.suffix not in {".md", ".base"}:
            continue
        relative = path.relative_to(vault)
        if any(part.startswith(".") for part in relative.parts):
            continue
        path_key = relative.as_posix()
        if path.suffix == ".md":
            path_key = path_key[:-3]
        path_key = path_key.casefold()
        by_path[path_key].add(path)
        name_key = path.stem if path.suffix == ".md" else path.name
        by_name[name_key.casefold()].add(path)

        if path.suffix != ".md":
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if not text.startswith("---\n"):
            continue
        try:
            metadata = parse_frontmatter(text, path.stem)
        except FrontmatterError:
            continue
        aliases = metadata.get("aliases")
        if isinstance(aliases, list):
            for alias in aliases:
                if isinstance(alias, str) and alias.strip():
                    by_name[alias.strip().casefold()].add(path)
    return by_path, by_name


def resolve_wikilink(
    raw_link: str,
    source: Path,
    link_index: tuple[dict[str, set[Path]], dict[str, set[Path]]],
) -> tuple[str, set[Path]]:
    """Resolve a wikilink target, leaving fragment validation to Obsidian."""
    target_with_fragment = raw_link.split("|", 1)[0].strip()
    target = re.split(r"[#^]", target_with_fragment, maxsplit=1)[0].strip()
    if not target:
        return target_with_fragment, {source}

    by_path, by_name = link_index
    normalized = target.replace("\\", "/").removeprefix("./").lstrip("/")
    if normalized.casefold().endswith(".md"):
        normalized = normalized[:-3]
    if "/" in normalized:
        matches = by_path.get(normalized.casefold(), set())
    else:
        matches = by_name.get(normalized.casefold(), set())
    return target_with_fragment, matches


def validate_completed_note(
    path: Path,
    metadata: dict[str, object],
    link_index: tuple[dict[str, set[Path]], dict[str, set[Path]]],
) -> list[str]:
    """Validate conservative content and semantic-link contracts."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        return [str(error)]

    errors: list[str] = []
    visible = visible_markdown(text)
    first_h1 = H1_RE.search(visible)
    if first_h1 is None:
        errors.append("missing required first H1")
    else:
        title = first_h1.group(1).strip()
        identities = {path.stem.casefold()}
        aliases = metadata.get("aliases")
        if isinstance(aliases, list):
            identities.update(
                alias.strip().casefold()
                for alias in aliases
                if isinstance(alias, str) and alias.strip()
            )
        if title.casefold() not in identities:
            errors.append(
                f"first H1 '{title}' must match the filename or one frontmatter alias"
            )

    if SUMMARY_RE.search(visible) is None:
        errors.append("missing required '## Summary' section")
    if metadata.get("type") == "knowledge" and SOURCES_RE.search(visible) is None:
        errors.append("missing required '## Sources' section")

    sentinel_content = without_code(text)
    for sentinel in sorted(set(TEMPLATE_SENTINEL_RE.findall(sentinel_content))):
        errors.append(f"unresolved template sentinel {sentinel!r}")

    for raw_link in WIKILINK_RE.findall(visible):
        target, matches = resolve_wikilink(raw_link, path, link_index)
        if not matches:
            errors.append(f"unresolved wikilink '{target}'")
        elif len(matches) > 1:
            errors.append(f"ambiguous wikilink '{target}'")
    return errors


def validate_wikilinks(
    path: Path,
    link_index: tuple[dict[str, set[Path]], dict[str, set[Path]]],
) -> list[str]:
    """Validate visible wikilinks without imposing a note content schema."""
    try:
        visible = visible_markdown(path.read_text(encoding="utf-8"))
    except OSError as error:
        return [str(error)]

    errors: list[str] = []
    for raw_link in WIKILINK_RE.findall(visible):
        target, matches = resolve_wikilink(raw_link, path, link_index)
        if not matches:
            errors.append(f"unresolved wikilink '{target}'")
        elif len(matches) > 1:
            errors.append(f"ambiguous wikilink '{target}'")
    return errors


def validate_artifact_metadata(
    metadata: dict[str, object], artifact_type: str
) -> list[str]:
    """Validate completed review and decision-record frontmatter."""
    errors: list[str] = []
    if artifact_type == "review":
        if metadata.get("type") != "review":
            errors.append("type must be 'review'")
        if metadata.get("review_type") != "knowledge":
            errors.append("review_type must be 'knowledge'")
        if not valid_iso_date(metadata.get("date")):
            errors.append("date must be an ISO date (YYYY-MM-DD)")
    elif artifact_type == "decision-record":
        if metadata.get("type") != "decision-record":
            errors.append("type must be 'decision-record'")
        status = metadata.get("status")
        if status not in VALID_DECISION_STATUSES:
            allowed = ", ".join(sorted(VALID_DECISION_STATUSES))
            errors.append(f"status must be one of: {allowed}")
        author = metadata.get("author")
        if not isinstance(author, str) or not author.strip():
            errors.append("author must be a nonempty string")
        if not valid_iso_date(metadata.get("created")):
            errors.append("created must be an ISO date (YYYY-MM-DD)")
    else:
        raise ValueError(f"unsupported artifact type: {artifact_type}")
    return errors


def validate_completed_artifact(
    path: Path,
    artifact_type: str,
    link_index: tuple[dict[str, set[Path]], dict[str, set[Path]]],
) -> list[str]:
    """Validate one completed review or decision record."""
    try:
        text = path.read_text(encoding="utf-8")
        metadata = parse_frontmatter(text, path.stem)
    except (OSError, FrontmatterError) as error:
        return [str(error)]

    errors = validate_artifact_metadata(metadata, artifact_type)
    if H1_RE.search(visible_markdown(text)) is None:
        errors.append("missing required first H1")
    for sentinel in sorted(set(TEMPLATE_SENTINEL_RE.findall(without_code(text)))):
        errors.append(f"unresolved template sentinel {sentinel!r}")
    errors.extend(validate_wikilinks(path, link_index))
    return errors


def load_registry(path: Path = REGISTRY) -> dict[str, dict[str, object]]:
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise RegistryError(str(error)) from error
    except json.JSONDecodeError as error:
        raise RegistryError(f"invalid JSON: {error.msg} on line {error.lineno}") from error

    if not isinstance(registry, dict) or not registry:
        raise RegistryError("registry must be a nonempty mapping")
    hubs: dict[str, str] = {}
    for domain, entry in registry.items():
        if not isinstance(domain, str) or not domain.strip():
            raise RegistryError("domain identifiers must be nonempty strings")
        if not isinstance(entry, dict):
            raise RegistryError(f"domain '{domain}' must map to an object")
        for field in ("hub_note", "description"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                raise RegistryError(f"domain '{domain}' field '{field}' must be a nonempty string")
        for field in ("includes", "excludes"):
            items = entry.get(field)
            if not isinstance(items, list) or any(
                not isinstance(item, str) or not item.strip() for item in items
            ):
                raise RegistryError(
                    f"domain '{domain}' field '{field}' must be a list of nonempty strings"
                )
        hub = entry["hub_note"]
        if hub in hubs:
            raise RegistryError(
                f"hub_note '{hub}' is assigned to both '{hubs[hub]}' and '{domain}'"
            )
        hubs[hub] = domain
    return registry


def valid_iso_date(value: object) -> bool:
    return parse_iso_date(value) is not None


def parse_iso_date(value: object) -> date | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def validate_string_list(
    metadata: dict[str, object], key: str, *, required: bool
) -> tuple[list[str] | None, list[str]]:
    value = metadata.get(key)
    if value is None:
        return None, [f"missing required {key}"] if required else []
    if not isinstance(value, list):
        return None, [f"{key} must be a list"]
    if not value:
        return value, [f"{key} must be a nonempty list"]
    if any(not isinstance(item, str) or not item.strip() for item in value):
        return value, [f"{key} must contain only nonempty strings"]
    if len(value) != len(set(value)):
        return value, [f"{key} must not contain duplicates"]
    return value, []


def validate_metadata(
    metadata: dict[str, object],
    controlled_domains: set[str],
    *,
    as_of: date | None = None,
) -> list[str]:
    errors: list[str] = []
    note_type = metadata.get("type")
    kind = metadata.get("kind")
    source_type = metadata.get("source_type")
    stance = metadata.get("stance")
    source_checked = metadata.get("source_checked")

    if note_type != "knowledge":
        errors.append("type must be 'knowledge'")
    if kind not in VALID_KINDS:
        errors.append(f"unsupported or missing kind '{kind or ''}'")
    if not valid_iso_date(metadata.get("created")):
        errors.append("created must be an ISO date (YYYY-MM-DD)")

    domains, domain_errors = validate_string_list(metadata, "domains", required=True)
    errors.extend(domain_errors)
    if domains and not domain_errors:
        if len(domains) > 3:
            errors.append("domains must contain between 1 and 3 values")
        unknown = [domain for domain in domains if domain not in controlled_domains]
        if unknown:
            errors.append(f"unknown domains: {', '.join(unknown)}")

    if "aliases" in metadata:
        _, alias_errors = validate_string_list(metadata, "aliases", required=False)
        errors.extend(alias_errors)
    if kind == "source":
        if not isinstance(source_type, str) or not source_type.strip():
            errors.append("kind 'source' requires source_type")
        elif source_type not in SOURCE_TYPE_SECTIONS:
            allowed = ", ".join(SOURCE_TYPE_SECTIONS)
            errors.append(
                f"unsupported source_type '{source_type}'; expected one of: {allowed}"
            )
    if kind != "source" and source_type is not None:
        errors.append("source_type is only valid with kind 'source'")
    if stance is not None and stance not in VALID_STANCES:
        errors.append(f"unsupported stance '{stance}'")
    if source_checked is not None:
        checked_date = parse_iso_date(source_checked)
        if checked_date is None:
            errors.append("source_checked must be an ISO date (YYYY-MM-DD)")
        elif checked_date > (as_of or date.today()):
            errors.append("source_checked must not be in the future")
    return errors


def validate_map_metadata(
    note_name: str,
    metadata: dict[str, object],
    registry: dict[str, dict[str, object]],
) -> list[str]:
    errors: list[str] = []
    map_for = metadata.get("map_for")
    hub_domains = {
        str(entry["hub_note"]): domain for domain, entry in registry.items()
    }
    configured_domain = hub_domains.get(note_name)

    if configured_domain is not None:
        if metadata.get("kind") != "synthesis":
            errors.append(f"configured hub must have kind 'synthesis', found '{metadata.get('kind') or ''}'")
        if map_for != configured_domain:
            errors.append(
                f"configured hub map_for must be '{configured_domain}', found '{map_for or ''}'"
            )
        if metadata.get("domains") != [configured_domain]:
            errors.append(f"configured hub domains must be exactly ['{configured_domain}']")
    elif map_for is not None:
        if map_for not in registry:
            errors.append(f"map_for references unregistered domain '{map_for}'")
        else:
            errors.append(
                f"map_for '{map_for}' is reserved for configured hub "
                f"'{registry[map_for]['hub_note']}'"
            )
    return errors


def validate_perspective_identity(
    note_names: set[str], note_metadata: dict[str, dict[str, object]]
) -> list[str]:
    errors: list[str] = []
    if PERSPECTIVE_NOTE not in note_names:
        errors.append(f"required perspective note is missing: Knowledge/{PERSPECTIVE_NOTE}.md")

    for name, metadata in note_metadata.items():
        if metadata.get("kind") == "perspective" and name != PERSPECTIVE_NOTE:
            errors.append(
                f"Knowledge/{name}.md: kind 'perspective' is reserved for "
                f"Knowledge/{PERSPECTIVE_NOTE}.md"
            )

    canonical = note_metadata.get(PERSPECTIVE_NOTE)
    if canonical is not None and canonical.get("kind") != "perspective":
        errors.append(
            f"Knowledge/{PERSPECTIVE_NOTE}.md: kind must be 'perspective'"
        )
    return errors


def validate_template_contracts(templates: Path = TEMPLATES) -> list[str]:
    contracts: dict[str, tuple[dict[str, object], str, tuple[str, ...]]] = {
        "Concept definition.md": (
            {"type": "knowledge", "kind": "concept", "domains": ["<domain>"]},
            "created",
            ("<domain>", "# {{title}}", "Replace every unresolved sentinel"),
        ),
        "Knowledge note.md": (
            {"type": "knowledge", "kind": "<kind>", "domains": ["<domain>"]},
            "created",
            ("<kind>", "<domain>", "# {{title}}", "Replace every unresolved sentinel"),
        ),
        "Domain map.md": (
            {
                "type": "knowledge",
                "kind": "synthesis",
                "map_for": "<domain>",
                "domains": ["<domain>"],
            },
            "created",
            ("<domain>", "# {{title}}", "Replace every unresolved sentinel"),
        ),
        "Knowledge review.md": (
            {"type": "review", "review_type": "knowledge"},
            "date",
            (
                "# Knowledge Review - {{date:YYYY-MM-DD}}",
                "<!-- Which notes informed a decision, explanation, conversation, or creation? -->",
            ),
        ),
        "Architecture Decision Record.md": (
            {"type": "decision-record", "status": "<status>", "author": "<author>"},
            "created",
            (
                "<status>",
                "<author>",
                "# ADR - {{title}}",
                "Replace every unresolved sentinel",
            ),
        ),
    }
    errors: list[str] = []
    for filename, (expected, date_field, sentinels) in contracts.items():
        path = templates / filename
        try:
            text = path.read_text(encoding="utf-8")
            metadata = parse_frontmatter(text, path.stem)
        except (OSError, FrontmatterError) as error:
            errors.append(f"Templates/{filename}: {error}")
            continue
        for key, value in expected.items():
            if metadata.get(key) != value:
                errors.append(f"Templates/{filename}: {key} must be {value!r}")
        if metadata.get(date_field) != "{{date:YYYY-MM-DD}}":
            errors.append(
                f"Templates/{filename}: {date_field} must be the quoted, parseable date placeholder"
            )
        for sentinel in sentinels:
            if sentinel not in text:
                errors.append(f"Templates/{filename}: missing required sentinel {sentinel!r}")
    return errors


def validate_hubs(
    registry: dict[str, dict[str, object]], note_names: set[str]
) -> list[str]:
    errors: list[str] = []
    for domain, entry in registry.items():
        hub = str(entry["hub_note"])
        if hub not in note_names:
            errors.append(f"configured hub for domain '{domain}' is missing: Knowledge/{hub}.md")
    return errors


def main() -> int:
    errors: list[str] = []
    validation_date = date.today()
    try:
        registry = load_registry()
    except RegistryError as error:
        print(f"ERROR: {REGISTRY.relative_to(VAULT)}: {error}")
        return 1

    errors.extend(validate_template_contracts())

    note_names = {
        path.stem
        for path in KNOWLEDGE.glob("*.md")
        if path.name != "Knowledge.md"
    }
    errors.extend(validate_hubs(registry, note_names))

    controlled_domains = set(registry)
    note_metadata: dict[str, dict[str, object]] = {}
    link_index = build_link_index()
    for directory, artifact_type in (
        (REVIEWS, "review"),
        (DECISIONS, "decision-record"),
    ):
        for path in sorted(directory.glob("*.md"), key=lambda item: item.name.casefold()):
            relative = path.relative_to(VAULT)
            errors.extend(
                f"{relative}: {error}"
                for error in validate_completed_artifact(path, artifact_type, link_index)
            )
    for path in USER_FACING_DOCUMENTS:
        relative = path.relative_to(VAULT)
        errors.extend(
            f"{relative}: {error}" for error in validate_wikilinks(path, link_index)
        )
    paths = (KNOWLEDGE / f"{name}.md" for name in note_names)
    for path in sorted(paths, key=lambda item: item.stem.casefold()):
        relative = path.relative_to(VAULT)
        try:
            metadata = frontmatter(path)
        except (OSError, FrontmatterError) as error:
            errors.append(f"{relative}: {error}")
            continue
        note_metadata[path.stem] = metadata
        errors.extend(
            f"{relative}: {error}"
            for error in validate_metadata(
                metadata, controlled_domains, as_of=validation_date
            )
        )
        errors.extend(
            f"{relative}: {error}"
            for error in validate_map_metadata(path.stem, metadata, registry)
        )
        errors.extend(
            f"{relative}: {error}"
            for error in validate_completed_note(path, metadata, link_index)
        )

    errors.extend(validate_perspective_identity(note_names, note_metadata))

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(
        f"Vault valid: {len(note_names)} completed Knowledge notes plus completed reviews "
        "and decisions, with user-facing wikilinks resolved, "
        "required content, valid frontmatter, controlled domains, and configured guides."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
