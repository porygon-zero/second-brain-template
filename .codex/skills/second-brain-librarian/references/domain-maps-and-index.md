# Controlled domains and guides

Load this reference when changing controlled domains, editing a domain guide, or proposing a domain.

## Authoritative classification

Knowledge frontmatter is the sole authoritative classification:

- `kind` records what a note represents.
- `domains` record one to three subjects to which it materially contributes.
- `.codex/skills/knowledge-domains.json` defines the controlled domains and names one guide for each.

`Knowledge/Knowledge Metadata Navigation Pilot.base` derives complete human navigation from this metadata. Do not maintain a second exhaustive identity registry or copy every domain assignment into Markdown maps.

## Domain guides

Each configured guide remains a human-readable `kind: synthesis` note with `map_for` and `domains` set to its single registry domain. It should contain:

- a strong summary of scope, exclusions, and boundary cases;
- a small set of selected entry points that help a person begin common questions;
- adjacent domains and useful tensions.

Selected entry points are curated routes, not complete membership, rankings, or endorsements. Change them only when doing so improves practical orientation.

After Knowledge or registry changes, run `python3 .codex/skills/second-brain-librarian/scripts/validate_taxonomy.py`.

## Community comparison

Run `scripts/analyze-communities` when the user requests an on-demand community analysis, a comparison between communities and domains, or a review of whether new domain scope may be emerging. Use `scripts/analyze-communities --json` when another flow needs structured output. Use `scripts/analyze-communities --publish` to update both `Reviews/Community-Domain Analysis - Latest.md` and the Obsidian graph's community colors. Publishing replaces only `.obsidian/graph.json`'s `colorGroups`; it preserves filters, forces, zoom, and other graph state.

The command derives communities from explicit wikilinks, excludes `Knowledge.md` and configured domain guides by default so navigation hubs do not dominate the topology, and compares each community with authoritative frontmatter domains. Its emergence signals identify patterns worth reading: coherent subcommunities inside a fragmented domain, cross-domain cohesion, and domain fragmentation.

Treat every community, centrality result, and emergence signal as a disposable diagnostic overlay. It may reflect linking habits, uneven note maturity, algorithm choice, or a useful theme that should remain cross-domain. Never infer truth, importance, stance, endorsement, personal agreement, or a taxonomy change from graph position. Read the candidate notes fully and use the proposal contract below before recommending a new domain. The default and JSON modes are read-only; publish mode changes only the latest review artifact and graph colors, never Knowledge notes, maps, domain assignments, or the registry.

During a knowledge review, or after a substantial batch of edits that materially changes wikilinks or domain assignments, inspect the community analysis. Refresh the published view when it would otherwise be materially stale. If a signal appears plausible after reading the implicated notes and current domain boundaries, offer the strongest well-supported domain proposal to the user, including alternatives such as an existing domain, multi-domain assignment, or better linking. Do not turn an algorithmic signal into a proposal without that note-level review.

## Domain proposals

A review may propose a domain but must not create, assign, or register it without explicit user approval. A proposal requires durable scope, several affected notes, a meaningful distinction from registered domains, concrete retrieval benefit, a proposed guide, and migration impact.
