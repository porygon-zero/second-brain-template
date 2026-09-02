#!/usr/bin/env python3
"""Compare derived wikilink communities with authoritative controlled domains."""

from __future__ import annotations

import argparse
import colorsys
import importlib.util
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path


VAULT = Path(__file__).resolve().parents[2]
VALIDATOR_PATH = (
    VAULT
    / ".codex"
    / "skills"
    / "second-brain-librarian"
    / "scripts"
    / "validate_taxonomy.py"
)
ALGORITHM = "deterministic-greedy-modularity-v1"
MIN_REVIEW_SIZE = 5
MIN_FRAGMENT_SIZE = 3
DOMINANT_DOMAIN_THRESHOLD = 0.80
CROSS_DOMAIN_THRESHOLD = 0.25
LATEST_REPORT = Path("Reviews/Community-Domain Analysis - Latest.md")
GRAPH_CONFIG = Path(".obsidian/graph.json")


def _load_validator():
    spec = importlib.util.spec_from_file_location("second_brain_taxonomy", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"could not load taxonomy parser from {VALIDATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _title(text: str, fallback: str) -> str:
    match = VALIDATOR.H1_RE.search(VALIDATOR.visible_markdown(text))
    return match.group(1).strip() if match else fallback


def read_notes(
    vault: Path, include_navigation: bool = False
) -> tuple[dict[str, dict[str, object]], list[str]]:
    knowledge = vault / "Knowledge"
    if not knowledge.is_dir():
        raise OSError(f"Knowledge directory not found: {knowledge}")

    notes: dict[str, dict[str, object]] = {}
    warnings: list[str] = []
    for path in sorted(knowledge.glob("*.md"), key=lambda item: item.name.casefold()):
        if path.name == "Knowledge.md" and not include_navigation:
            continue
        try:
            text = path.read_text(encoding="utf-8")
            metadata = (
                {}
                if path.name == "Knowledge.md"
                else VALIDATOR.parse_frontmatter(text, path.stem)
            )
        except (OSError, UnicodeError, VALIDATOR.FrontmatterError) as error:
            warnings.append(f"{path.relative_to(vault)}: {error}")
            continue

        is_navigation = path.name == "Knowledge.md" or metadata.get("map_for") is not None
        if is_navigation and not include_navigation:
            continue
        domains = metadata.get("domains", [])
        if not isinstance(domains, list):
            domains = []
        visible = VALIDATOR.visible_markdown(text)
        notes[path.relative_to(vault).as_posix()] = {
            "path": path,
            "title": _title(text, path.stem),
            "domains": [domain for domain in domains if isinstance(domain, str)],
            "links": VALIDATOR.WIKILINK_RE.findall(visible),
            "navigation": is_navigation,
        }
    return notes, warnings


def build_graph(
    vault: Path, notes: dict[str, dict[str, object]], warnings: list[str]
) -> dict[str, set[str]]:
    graph = {node: set() for node in notes}
    included_paths = {Path(str(note["path"])).resolve(): node for node, note in notes.items()}
    link_index = VALIDATOR.build_link_index(vault)

    for source, note in notes.items():
        source_path = Path(str(note["path"])).resolve()
        links = note["links"]
        if not isinstance(links, list):
            continue
        for raw_link in links:
            _, matches = VALIDATOR.resolve_wikilink(str(raw_link), source_path, link_index)
            if len(matches) > 1:
                warnings.append(f"{source}: ambiguous wikilink [[{raw_link}]] ignored")
                continue
            if not matches:
                warnings.append(f"{source}: unresolved wikilink [[{raw_link}]] ignored")
                continue
            target = included_paths.get(next(iter(matches)).resolve())
            if target is None or target == source:
                continue
            graph[source].add(target)
            graph[target].add(source)
    return graph


def connected_components(graph: dict[str, set[str]]) -> list[set[str]]:
    unseen = set(graph)
    components: list[set[str]] = []
    while unseen:
        root = min(unseen)
        unseen.remove(root)
        component = {root}
        stack = [root]
        while stack:
            node = stack.pop()
            for neighbor in sorted(graph[node] & unseen):
                unseen.remove(neighbor)
                component.add(neighbor)
                stack.append(neighbor)
        components.append(component)
    return sorted(components, key=lambda group: (-len(group), min(group)))


def detect_communities(graph: dict[str, set[str]]) -> list[set[str]]:
    """Merge adjacent groups while doing so increases undirected modularity."""
    edge_count = sum(len(neighbors) for neighbors in graph.values()) / 2
    if edge_count == 0:
        return [{node} for node in sorted(graph)]

    ordered_nodes = sorted(graph)
    communities = {index: {node} for index, node in enumerate(ordered_nodes)}
    membership = {node: index for index, node in enumerate(ordered_nodes)}

    while True:
        degrees = {
            community: sum(len(graph[node]) for node in members)
            for community, members in communities.items()
        }
        between: Counter[tuple[int, int]] = Counter()
        for node, neighbors in graph.items():
            left = membership[node]
            for neighbor in neighbors:
                if node >= neighbor:
                    continue
                right = membership[neighbor]
                if left != right:
                    between[tuple(sorted((left, right)))] += 1

        candidates: list[tuple[float, int, int, int, int]] = []
        for (left, right), crossing_edges in between.items():
            delta = (
                crossing_edges / edge_count
                - degrees[left] * degrees[right] / (2 * edge_count * edge_count)
            )
            candidates.append((delta, -min(left, right), -max(left, right), left, right))
        if not candidates:
            break
        delta, _, _, left, right = max(candidates)
        if delta <= 0:
            break

        keep, remove = min(left, right), max(left, right)
        communities[keep] |= communities.pop(remove)
        for node in communities[keep]:
            membership[node] = keep

    return sorted(communities.values(), key=lambda group: (-len(group), min(group)))


def _domain_rows(
    registry: dict[str, dict[str, object]],
    notes: dict[str, dict[str, object]],
    communities: list[set[str]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for domain in sorted(registry):
        members = {
            node for node, note in notes.items() if domain in note.get("domains", [])
        }
        distribution = []
        for index, community in enumerate(communities, start=1):
            count = len(members & community)
            if count:
                distribution.append({"community": f"C{index:02}", "count": count})
        distribution.sort(key=lambda item: (-int(item["count"]), str(item["community"])))
        dominant_share = (
            int(distribution[0]["count"]) / len(members) if members and distribution else 0.0
        )
        rows.append(
            {
                "domain": domain,
                "note_count": len(members),
                "community_count": len(distribution),
                "dominant_share": dominant_share,
                "distribution": distribution,
            }
        )
    return rows


def _community_rows(
    notes: dict[str, dict[str, object]],
    graph: dict[str, set[str]],
    communities: list[set[str]],
    domain_rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    domain_members = {
        str(row["domain"]): {
            node for node, note in notes.items() if row["domain"] in note.get("domains", [])
        }
        for row in domain_rows
    }
    rows: list[dict[str, object]] = []
    for index, members in enumerate(communities, start=1):
        overlaps = []
        for domain, assigned in domain_members.items():
            count = len(members & assigned)
            if not count:
                continue
            overlaps.append(
                {
                    "domain": domain,
                    "count": count,
                    "community_share": count / len(members),
                    "domain_share": count / len(assigned),
                    "jaccard": count / len(members | assigned),
                }
            )
        overlaps.sort(
            key=lambda item: (
                -int(item["count"]),
                -float(item["jaccard"]),
                str(item["domain"]),
            )
        )
        internal_edges = sum(len(graph[node] & members) for node in members) // 2
        possible_edges = len(members) * (len(members) - 1) / 2
        central = sorted(
            members,
            key=lambda node: (
                -len(graph[node] & members),
                -len(graph[node]),
                str(notes[node]["title"]).casefold(),
            ),
        )[:6]
        rows.append(
            {
                "community": f"C{index:02}",
                "size": len(members),
                "internal_edges": internal_edges,
                "density": internal_edges / possible_edges if possible_edges else 0.0,
                "domain_overlaps": overlaps,
                "central_notes": [str(notes[node]["title"]) for node in central],
                "members": [
                    {
                        "title": str(notes[node]["title"]),
                        "file": node,
                        "domains": notes[node]["domains"],
                    }
                    for node in sorted(
                        members, key=lambda node: str(notes[node]["title"]).casefold()
                    )
                ],
            }
        )
    return rows


def _review_signals(
    communities: list[dict[str, object]], domains: list[dict[str, object]]
) -> list[dict[str, object]]:
    domain_by_name = {str(row["domain"]): row for row in domains}
    signals: list[dict[str, object]] = []

    for community in communities:
        size = int(community["size"])
        overlaps = community["domain_overlaps"]
        if size < MIN_REVIEW_SIZE or not isinstance(overlaps, list) or not overlaps:
            continue
        dominant = overlaps[0]
        dominant_name = str(dominant["domain"])
        dominant_share = float(dominant["community_share"])
        domain_row = domain_by_name[dominant_name]
        substantial_fragments = [
            item
            for item in domain_row["distribution"]
            if int(item["count"]) >= MIN_FRAGMENT_SIZE
        ]

        if (
            dominant_share >= DOMINANT_DOMAIN_THRESHOLD
            and float(domain_row["dominant_share"]) < DOMINANT_DOMAIN_THRESHOLD
            and len(substantial_fragments) >= 2
        ):
            signals.append(
                {
                    "signal": "coherent-subcommunity",
                    "community": community["community"],
                    "note_count": size,
                    "current_domain": dominant_name,
                    "evidence": (
                        f"{float(dominant['community_share']):.0%} of the community belongs "
                        f"to {dominant_name}, while that domain is distributed across "
                        f"{len(substantial_fragments)} substantial communities"
                    ),
                    "central_notes": community["central_notes"],
                }
            )
            continue

        cross_domain = [
            item
            for item in overlaps
            if float(item["community_share"]) >= CROSS_DOMAIN_THRESHOLD
        ]
        if dominant_share < DOMINANT_DOMAIN_THRESHOLD and len(cross_domain) >= 2:
            signals.append(
                {
                    "signal": "cross-domain-cohesion",
                    "community": community["community"],
                    "note_count": size,
                    "current_domains": [str(item["domain"]) for item in cross_domain],
                    "evidence": (
                        "no single domain covers 80% of the community, while multiple "
                        "domains each cover at least 25%"
                    ),
                    "central_notes": community["central_notes"],
                }
            )

    for domain in domains:
        substantial_fragments = [
            item
            for item in domain["distribution"]
            if int(item["count"]) >= MIN_FRAGMENT_SIZE
        ]
        if (
            int(domain["note_count"]) >= MIN_REVIEW_SIZE
            and float(domain["dominant_share"]) < DOMINANT_DOMAIN_THRESHOLD
            and len(substantial_fragments) >= 2
        ):
            signals.append(
                {
                    "signal": "domain-fragmentation",
                    "domain": domain["domain"],
                    "note_count": domain["note_count"],
                    "evidence": (
                        f"the largest community contains only "
                        f"{float(domain['dominant_share']):.0%} of the domain across "
                        f"{len(substantial_fragments)} substantial communities"
                    ),
                    "distribution": substantial_fragments,
                }
            )
    return signals


def analyze(vault: Path, include_navigation: bool = False) -> dict[str, object]:
    vault = vault.resolve()
    registry = VALIDATOR.load_registry(vault / ".codex" / "skills" / "knowledge-domains.json")
    notes, warnings = read_notes(vault, include_navigation=include_navigation)
    graph = build_graph(vault, notes, warnings)
    detected = detect_communities(graph)
    domains = _domain_rows(registry, notes, detected)
    communities = _community_rows(notes, graph, detected, domains)
    components = connected_components(graph)
    return {
        "schema_version": 1,
        "algorithm": ALGORITHM,
        "authority": {
            "domains": "authoritative frontmatter classification",
            "communities": "derived diagnostic overlay",
            "review_signals": "candidates for human review, not domain proposals",
        },
        "graph": {
            "nodes": len(graph),
            "edges": sum(len(neighbors) for neighbors in graph.values()) // 2,
            "isolates": sum(not neighbors for neighbors in graph.values()),
            "connected_components": [len(component) for component in components],
            "navigation_included": include_navigation,
        },
        "communities": communities,
        "domains": domains,
        "review_signals": _review_signals(communities, domains),
        "warnings": sorted(set(warnings)),
    }


def render_text(report: dict[str, object]) -> str:
    graph = report["graph"]
    lines = [
        "Community-domain analysis",
        f"Algorithm: {report['algorithm']}",
        (
            f"Graph: {graph['nodes']} notes, {graph['edges']} wikilink edges, "
            f"{graph['isolates']} isolates, components {graph['connected_components']}"
        ),
        "Communities are derived diagnostics; domains remain authoritative.",
        "",
        "Communities",
    ]
    for community in report["communities"]:
        if int(community["size"]) < 2:
            continue
        overlaps = ", ".join(
            f"{item['domain']} {item['count']}/{community['size']} "
            f"({float(item['community_share']):.0%})"
            for item in community["domain_overlaps"][:4]
        )
        lines.extend(
            [
                (
                    f"{community['community']}: {community['size']} notes, "
                    f"{community['internal_edges']} internal edges"
                ),
                f"  Domain overlap: {overlaps or 'none'}",
                f"  Central notes: {', '.join(community['central_notes'])}",
            ]
        )

    lines.extend(["", "Domains"])
    for domain in report["domains"]:
        distribution = ", ".join(
            f"{item['community']}:{item['count']}" for item in domain["distribution"]
        )
        lines.append(
            f"{domain['domain']}: {domain['note_count']} notes across "
            f"{domain['community_count']} communities; dominant share "
            f"{float(domain['dominant_share']):.0%} [{distribution}]"
        )

    lines.extend(["", "Emergence review signals (not domain proposals)"])
    if report["review_signals"]:
        for signal in report["review_signals"]:
            subject = signal.get("community", signal.get("domain", "unknown"))
            lines.append(f"- {signal['signal']} — {subject}: {signal['evidence']}")
    else:
        lines.append("- None under the conservative default thresholds.")
    lines.extend(
        [
            "",
            "Before proposing a domain, read the candidate notes and establish durable scope,",
            "a meaningful distinction, retrieval benefit, a proposed guide, and migration impact.",
        ]
    )
    warnings = report["warnings"]
    if warnings:
        lines.extend(["", f"Warnings: {len(warnings)}"])
        lines.extend(f"- {warning}" for warning in warnings)
    return "\n".join(lines)


def render_markdown(report: dict[str, object], analyzed_on: date) -> str:
    """Render the complete latest analysis as a human-readable Obsidian note."""
    graph = report["graph"]
    lines = [
        "---",
        "type: review",
        "review_type: knowledge",
        f"date: {analyzed_on.isoformat()}",
        f"analyzed: {analyzed_on.isoformat()}",
        "---",
        "",
        "# Community-Domain Analysis - Latest",
        "",
        f"> Analyzed {analyzed_on.isoformat()} with `{report['algorithm']}`. This is a derived diagnostic overlay; controlled domains remain authoritative.",
        "",
        "## Graph summary",
        "",
        f"- Notes: {graph['nodes']}",
        f"- Wikilink edges: {graph['edges']}",
        f"- Isolates: {graph['isolates']}",
        f"- Connected components: {graph['connected_components']}",
        f"- Navigation notes included: {'yes' if graph['navigation_included'] else 'no'}",
        "",
        "## Detected communities",
        "",
    ]
    for community in report["communities"]:
        overlaps = ", ".join(
            f"`{item['domain']}` {item['count']}/{community['size']} ({float(item['community_share']):.0%})"
            for item in community["domain_overlaps"][:6]
        )
        lines.extend(
            [
                f"### {community['community']} - {community['size']} notes",
                "",
                f"- Internal edges: {community['internal_edges']}",
                f"- Density: {float(community['density']):.3f}",
                f"- Graph color: `#{_community_color(int(str(community['community'])[1:]) - 1):06X}`",
                f"- Domain overlap: {overlaps or 'none'}",
                f"- Central notes: {', '.join(f'[[{title}]]' for title in community['central_notes'])}",
                "- Members:",
            ]
        )
        for member in community["members"]:
            domains = ", ".join(f"`{domain}`" for domain in member["domains"]) or "none"
            lines.append(f"  - [[{member['title']}]] - domains: {domains}")
        lines.append("")

    lines.extend(["## Domain distribution", ""])
    for domain in report["domains"]:
        distribution = ", ".join(
            f"{item['community']} {item['count']}" for item in domain["distribution"]
        )
        lines.append(
            f"- `{domain['domain']}`: {domain['note_count']} notes across "
            f"{domain['community_count']} communities; dominant share "
            f"{float(domain['dominant_share']):.0%} ({distribution or 'no included notes'})"
        )

    lines.extend(["", "## Emergence review signals", ""])
    if report["review_signals"]:
        for signal in report["review_signals"]:
            subject = signal.get("community", signal.get("domain", "unknown"))
            lines.append(f"- **{signal['signal']} - {subject}:** {signal['evidence']}.")
    else:
        lines.append("- None under the conservative default thresholds.")
    lines.extend(
        [
            "",
            "These signals are prompts for note-level review, not domain proposals. Before proposing a domain, the Librarian must read the implicated notes and establish durable scope, a meaningful distinction from existing domains, retrieval benefit, a proposed guide, and migration impact.",
        ]
    )
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {warning}" for warning in report["warnings"])
    return "\n".join(lines) + "\n"


def _community_color(index: int) -> int:
    """Return deterministic, saturated colors distributed around the hue wheel."""
    hue = (0.08 + index * 0.618033988749895) % 1.0
    red, green, blue = colorsys.hsv_to_rgb(hue, 0.62, 0.88)
    return (round(red * 255) << 16) | (round(green * 255) << 8) | round(blue * 255)


def _path_query(path: str) -> str:
    escaped = path.replace("\\", "\\\\").replace('"', '\\"')
    return f'path:"{escaped}"'


def community_color_groups(report: dict[str, object]) -> list[dict[str, object]]:
    groups = []
    for index, community in enumerate(report["communities"]):
        query = " OR ".join(_path_query(member["file"]) for member in community["members"])
        groups.append({"query": query, "color": {"a": 1, "rgb": _community_color(index)}})
    groups.append(
        {"query": 'path:"Knowledge"', "color": {"a": 1, "rgb": 0x858B98}}
    )
    return groups


def publish(report: dict[str, object], vault: Path, analyzed_on: date) -> tuple[Path, Path]:
    """Publish the latest note and replace only graph color groups."""
    vault = vault.resolve()
    report_path = vault / LATEST_REPORT
    graph_path = vault / GRAPH_CONFIG
    if not graph_path.is_file():
        raise OSError(f"Obsidian graph configuration not found: {graph_path}")

    graph_text = graph_path.read_text(encoding="utf-8")
    graph_config = json.loads(graph_text)
    if not isinstance(graph_config, dict) or not isinstance(graph_config.get("colorGroups"), list):
        raise OSError(f"invalid Obsidian graph configuration: {graph_path}")
    graph_config["colorGroups"] = community_color_groups(report)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_markdown(report, analyzed_on), encoding="utf-8")
    rendered_graph = json.dumps(graph_config, indent=2, ensure_ascii=False)
    if graph_text.endswith("\n"):
        rendered_graph += "\n"
    graph_path.write_text(rendered_graph, encoding="utf-8")
    return report_path, graph_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare derived wikilink communities with controlled domains."
    )
    parser.add_argument(
        "--json", action="store_true", help="emit deterministic machine-readable output"
    )
    parser.add_argument(
        "--include-navigation",
        action="store_true",
        help="include Knowledge.md and domain maps, which may behave as graph hubs",
    )
    parser.add_argument(
        "--publish",
        action="store_true",
        help="write the latest review note and replace Obsidian graph color groups",
    )
    parser.add_argument("--vault", type=Path, default=VAULT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.json and args.publish:
        parser.error("--json and --publish cannot be used together")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        report = analyze(args.vault, include_navigation=args.include_navigation)
        published = publish(report, args.vault, date.today()) if args.publish else None
    except (OSError, json.JSONDecodeError, VALIDATOR.RegistryError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    else:
        print(render_text(report))
    if published:
        print(f"\nPublished: {published[0].relative_to(args.vault.resolve())}")
        print(f"Graph colors: {published[1].relative_to(args.vault.resolve())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
