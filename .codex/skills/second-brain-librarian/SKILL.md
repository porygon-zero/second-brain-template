---
name: second-brain-librarian
description: Edits and maintains this AI-assisted Obsidian Second Brain vault. Use when the user asks to add, capture, import, research and save, create, review and improve, distill, organize, connect, update, rename, move, consolidate, archive, or remove vault knowledge, including persisting explicitly confirmed perspective from reflection or interviews. Do NOT use for neutral read-only expertise; use second-brain-expert. Do NOT use for perspective-aware reflection, counsel, or interviews that should not yet be saved; use second-brain-interlocutor. Do not use for Codex or skill configuration changes themselves.
---

# Second Brain Librarian

Maintain this vault as the Resources portion of PARA and use the Capture, Organize, Distill, Express (CODE) workflow to turn durable information into reusable insight and concrete output. Keep Projects, Areas, tasks, meetings, daily logs, organization-specific operations, and responsibility management outside it. Store focused, durable knowledge in `Knowledge/`; treat AI-created notes as source-grounded synthesis, never assumed personal beliefs.

## Core contract

- Inspect relevant notes before changing files. Use domain maps, direct links, focused file/content search, or the shared retrieval helper for targeted candidate selection. The helper is optional acceleration, not a gate to vault knowledge. Read relevant evidence fully and prefer a suitable existing note over a duplicate.
- Classify what a note represents with `kind` independently from the subjects it materially contributes to with controlled `domains`. Frontmatter is authoritative; navigation views and maps are derived aids.
- Preserve distinctions among source claims, authored synthesis, assistant inference, tensions, and explicitly recorded personal perspective. Never fabricate personal resonance, intended use, support, citations, page numbers, agreement, or certainty.
- Capture material because it is durably relevant, not only because it agrees with the maintained perspective. Preserve serious counterevidence and alternatives; relevance does not imply endorsement.
- Record interview-derived beliefs, priorities, red lines, exceptions, or tensions only after the user explicitly confirms their substance. Preserve rejected or unresolved interpretations as such only when the user asks to save them.
- Use sources proportionately: routine learning may use clearly scoped secondary orientation, while consequential or time-sensitive material requires live verification against decision-grade sources even when a note is polished or previously checked.
- Use `[[wikilinks]]` internally and standard Markdown links externally. Add only meaningful semantic relationships; shared domains and word overlap are not relationships.
- Optimize for `Information that resonates -> discoverable note -> reusable insight -> concrete expression`, not note count, completeness, taxonomy, uniformity, or graph density.
- When directly developing and saving a substantial artifact, follow the shared production-mode protocol before writing. When preserving an existing artifact, retain its authorship and epistemic status rather than treating persistence as endorsement or confirmed Perspective.
- Do not edit `.obsidian/`, change vault architecture, create new metadata systems, or reorganize the entire vault unless explicitly requested.
- Ask before deleting, merging, moving, or archiving notes unless the user explicitly requested that exact operation. Exact authority is bounded to the named action and targets; do not expand it into adjacent cleanup.

## Load task-specific guidance

Read each relevant file completely before acting; all references are one level from this file:

- [knowledge-model-and-source-rules.md](references/knowledge-model-and-source-rules.md) — read before classifying Knowledge, editing controlled metadata, interpreting personal perspective, or handling provenance and external sources.
- [create-or-improve-knowledge.md](references/create-or-improve-knowledge.md) — read for capture, import, research-and-save, creation, editing, organization, connection, or distillation.
- [domain-maps-and-index.md](references/domain-maps-and-index.md) — read when analyzing communities, comparing communities with controlled domains, changing domains, editing a domain guide, or proposing a domain.
- [second-brain-perspective.md](references/second-brain-perspective.md) — read and apply the Perspective impact gate after every operation that creates, edits, moves, merges, or removes a note in `Knowledge/`; read the full Perspective note only when the gate triggers.
- [review-and-expression.md](references/review-and-expression.md) — read for vault review, critique with changes, distilling toward an output, or saving reusable synthesis.
- [artifact-development.md](../artifact-development.md) — read when directly developing and saving a substantial presentation, article, report, workshop, proposal, or comparable artifact.

## Required mutation workflow

1. Inspect the target, relevant context, controlled-domain registry, and templates needed for the requested scope.
2. For a correction, merge, archive, or removal, search for inbound links and material claims derived from the affected note. Update or remove stale dependents within the authorized operation; if propagation requires an unapproved destructive or location-changing action, stop and ask rather than leaving known stale knowledge.
3. Make the smallest durable change and preserve provenance and epistemic distinctions.
4. Maintain affected meaningful links. Update a domain guide only when its scope, boundary, or curated entry points materially change; complete membership is derived from frontmatter.
5. Apply the Perspective impact gate after every `Knowledge/` operation. When it triggers, read `Knowledge/Second Brain Perspective.md` completely and change it only for a material perspective update; otherwise skip the full read.
6. After Knowledge changes, run `python3 .codex/skills/second-brain-librarian/scripts/validate_taxonomy.py` and resolve every error. Use `scripts/check-vault` when the encompassing integrity check is required.
7. Report changed files, validation performed and its actual result, the required Perspective gate outcome and reason, propagation checked and handled, what was omitted, and material uncertainty. Never hide a failed or unavailable check.

For an explicit community/domain comparison or taxonomy-emergence review, run `scripts/analyze-communities`. Use `scripts/analyze-communities --publish` when the user asks to refresh the visible graph or latest report, and after a substantial batch of relationship or domain changes that would make the published view materially stale. Treat its communities and review signals as derived diagnostic evidence only. When a plausible emergence signal appears, read the implicated notes before interpreting the cluster and apply the domain-proposal contract before offering a new-domain proposal. Do not silently create, assign, or register the proposed domain.

Do not create or assign an unregistered domain, add another `kind: perspective`, or change the registry without explicit user approval. If a supplied reference is inaccessible or only partly visible, say so and do not imply broader review.

## Human documentation contract

`SYSTEM_GUIDE.md` is the canonical human overview. When an authorized change alters Librarian routing, authority, persistence, validation, the knowledge model, or another visible vault workflow, update the guide in the same change. Pure content additions normally do not require a guide update. Report the documentation impact in the completion summary.
