# Knowledge model and source rules

Load this reference before classifying Knowledge, editing controlled metadata, interpreting perspective, or handling sources.

## Identity

Classify what a note represents, not merely its topic or how its ideas may be reused:

| Note identity | Frontmatter |
|---|---|
| General topic or reusable idea | `kind: concept` |
| Named reusable structure | `kind: framework`, `method`, or `principle` |
| One named publication or external resource | `kind: source` plus `source_type` |
| Maintained, provisional vault orientation | `kind: perspective` |
| View assembled across multiple notes | `kind: synthesis` |

The complete controlled source types are the exact lowercase values `book`, `article`, `paper`, `report`, and `website`; do not normalize typos, case variants, or unrecognized resource types. Source identity takes precedence over subject: a note substantially representing one titled work remains `kind: source` even when it extracts reusable ideas. Use `framework`, `method`, or `principle` when the reusable structure itself is the subject and the note is not primarily about one publication.

Determine identity from title, summary, provenance, and sources before accepting a template default. When uncertain ask: “Would a future reader expect this note under the title of one specific work, or under a reusable idea or structure independent of that work?”

`kind: perspective` is distinct from ordinary synthesis and is not automatically the user's beliefs. Exactly `Knowledge/Second Brain Perspective.md` currently fills it. Another perspective identity is a taxonomy decision requiring explicit user approval.

Frontmatter is authoritative. Complete identity and domain views are derived by `Knowledge/Knowledge Metadata Navigation Pilot.base`; do not duplicate files or maintain a parallel alphabetical registry.

## Controlled domains and relationships

Every note in `Knowledge/` requires one to three exact identifiers from `.codex/skills/knowledge-domains.json`. Assign by material contribution, normally one; use two or three only for genuine bridge notes. Never invent, normalize, assign, or register a domain silently. If none fits, surface the mismatch and ask before changing the registry.

The registry maps each domain one-to-one to a human-readable guide. Each guide is `kind: synthesis`, has `map_for` equal to its own domain, and lists exactly that one domain in `domains`.

Link notes with meaningful predicates such as `Supports`, `Challenges`, `Applies`, `Extends`, `Deepens`, and `Provides`. A book can inform several concepts. Do not use shared domains or word overlap as a substitute for a relationship.

## Stance, epistemics, and sources

Treat `stance` as categorical, not a strength ranking:

- `adopted`: an explicit user commitment.
- `aligned`: fits documented personal perspectives without proving commitment.
- `exploring`: a position under consideration.
- `contested`: material disagreement or unresolved conflict.
- `reference`: useful context without a position.

Omit `stance` when one value would misrepresent a multi-position note. Never infer endorsement or personal belief from interest, note content, synthesis, stance, frequency, domains, or graph centrality.

Put source claims in `## Source-grounded notes`, normative authored synthesis in `## Principles and implications`, objections and conflicts in `## Tensions`, and assistant deductions in `## Questions and inferences`. Add `## Personal perspective` only for explicitly recorded, user-supplied reactions, experiences, or conclusions. Polished synthesis must not obscure weak or conflicting evidence.

Record enough provenance to recover a source: author, title, URL or publication, and access date when available. Keep per-source access dates in `## Sources`.

Set `source_checked: YYYY-MM-DD` only after opening cited sources and checking them against the note's material claims on that date, and never set it later than the current date. It proves neither source authority, currentness, nor fitness for a decision. Update it only after repeating that verification, never for editorial changes or reviews of vault notes. Leave it absent when no verification date is known; absence does not mean falsehood.

Use evidence proportionately. Commercial and secondary explainers may orient routine learning. For legal, regulatory, financial, safety-critical, operational, price, current-product, or otherwise consequential use, verify live even when the note is polished or previously checked. Prefer official or primary authorities and original publications; triangulate contested or consequential claims; and record the relevant jurisdiction and an `as of` date in prose when applicable. Disclose inaccessible material and the scope actually checked. Abstracts, excerpts, and previews support only claims within their visible scope and never justify implying full-text review.
