# Vault Conventions

## Keep durable knowledge

Use `Knowledge/` for focused information worth retrieving and reusing. Use `Inbox/` for temporary capture, `Reviews/` for reviews, `Decisions/` for durable decisions, and `Exports/` for generated output. This vault is not required to hold tasks, meetings, or every source you encounter.

## Classify notes

Every completed Knowledge note has frontmatter with `type: knowledge`, a supported `kind`, an ISO `created` date, and one to three domains registered in `.codex/skills/knowledge-domains.json`.

`kind` says what the note represents. `domains` say which subjects it materially contributes to. A source note may be relevant without being endorsed.

## Write complete notes

Use a template from `Templates/`. Replace every placeholder and include:

- one H1 matching the filename or a declared alias;
- a concise `## Summary`;
- enough prose to make the idea reusable;
- meaningful Obsidian wikilinks where relationships exist; and
- a `## Sources` section that states the actual provenance.

Use standard Markdown links for external URLs. Do not invent citations, page numbers, access, agreement, or certainty.

## Maintain domains

Each controlled domain has one map named by its registry `hub_note`. The map defines scope and offers a few useful entry points. Add a domain only when several real notes need a distinct durable retrieval boundary; do not create taxonomy for hypothetical content.

## Maintain perspective

`Knowledge/Second Brain Perspective.md` is the only perspective note. Record beliefs, priorities, boundaries, or commitments only after explicit user confirmation. Interest, repetition, links, and note selection do not establish personal belief.

## Validate changes

Run `scripts/check-vault` after structural changes. Validation checks contracts and links; it does not establish truth or quality.
