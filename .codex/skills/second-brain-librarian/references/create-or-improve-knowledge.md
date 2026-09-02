# Create or improve Knowledge

Load this reference for capture, import, research-and-save, creation, editing, organization, connection, or distillation.

## Progressive retrieval

For targeted work, use domain maps, direct links, focused file/content search, or, when helpful, `python3 <vault>/.codex/skills/retrieve_knowledge.py "<query>"` from any working directory. The helper is optional acceleration, not a gate to vault knowledge. Its default four-result shortlist ranks exact title and alias matches first, then title, `## Summary`, and controlled-domain evidence, and finally unions low-weight matches from visible full-note prose; comments and code do not contribute. Use `--limit N` to request as many candidates as the task requires or `--json` for machine-readable output. Treat scores as candidate-selection rationale, not evidence, and treat the default shortlist as a starting point rather than a context limit. Read full notes after selecting promising candidates, continuing until the material concepts, named frameworks or sources, adjacent or contrary positions, and relevant provenance are adequately covered. If unusual language or conceptual synonyms require semantic nuance the helper misses, use focused manual searches; avoid raw broad-search output that adds no task-relevant information.

For broad maintenance or orientation, use the relevant domain-guide summaries and selected entry points, then use the helper to select only notes that can materially affect the edit. Search before researching or writing; never load the whole vault by default.

## Workflow

1. Identify the likely future use and smallest durable scope. Capture selectively: useful ideas, examples, facts, questions, quotations, and experiences.
2. Read supplied references. If the note will inform a consequential or time-sensitive use, apply the live-verification contract in `knowledge-model-and-source-rules.md`; otherwise keep research proportionate. Report inaccessible or partly visible material and do not imply broader review.
3. Preserve provenance and distinguish source claims, authored synthesis, assistant inference, tensions, and explicitly recorded personal perspective.
4. Classify the note by identity before accepting any template default, then assign one to three controlled domains independently by material contribution.
5. Update a suitable existing note whenever possible. Otherwise choose the template by output identity:
   - `Templates/Concept definition.md` for a concise `kind: concept` definition.
   - `Templates/Knowledge note.md` for a substantial source, framework, method, principle, or synthesis.
   - `Templates/Domain map.md` only for a registered domain map.
   - Perspective has no generic creation template and must not use `Templates/Knowledge note.md`; another Perspective requires explicit taxonomy approval.
6. Treat a file as a template because of its location and filename in `Templates/`; its frontmatter describes the prospective output. Replace every visible sentinel, including angle-bracket placeholders and bracketed or example fields, before using the result. Use ISO dates (`YYYY-MM-DD`).
7. Add only meaningful semantic relationships.
8. Complete membership is derived from frontmatter. Update a domain guide only when the new note materially improves its scope, boundary explanation, or small set of selected entry points.
9. Apply the required Perspective impact gate, validation, and final reporting from `SKILL.md`.

## Organize and distill

- Put each note in one primary place under `Knowledge/`. Keep Projects, Areas, execution, responsibilities, tasks, meetings, and daily logs outside this vault.
- Use generated Knowledge views and search for complete discovery; use semantic wikilinks for meaningful relationships.
- Archive only when requested or clearly warranted, and obtain authority before moving material.
- Design for an impatient future self: make `## Summary` the executive-summary layer and preserve caveats and source context below it.
- Add emphasis or highlighting only when a real revisit benefits. Improve notes for a concrete future use, not cosmetic consistency.
- Do not indiscriminately clip, create dumping-ground notes, redundant tags, metadata, folders, or status systems.

## Correct and retire

- Correct the durable claim at its maintained source rather than appending a contradictory addendum that leaves the old claim active.
- Search the vault for inbound wikilinks, title and alias references, quotations, and material downstream claims before completing a correction, merge, archive, or removal. Do not treat a clean wikilink validator as proof that semantic propagation is complete.
- Preserve provenance for the correction when it materially affects trust or interpretation. Do not retain superseded content merely to simulate an append-only memory unless its history remains useful and clearly labeled.
- For an authorized removal, remove stale references and revise dependent claims that no longer have support. Ask before any additional merge, move, archive, or deletion not already authorized.
