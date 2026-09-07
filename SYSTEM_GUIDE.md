# Second Brain System Guide

## How it works

The vault is a folder of Markdown files. Obsidian reads and edits those files. AI skills retrieve relevant files and operate under one of three authority levels:

```text
Question or source
       |
       +-- Expert: neutral answer, read-only
       +-- Interlocutor: perspective-aware reflection, read-only
       +-- Librarian: authorized durable change
```

The files remain usable without AI. Search and retrieval help locate candidate notes; they do not make a note true or turn a source's claim into your belief.

## Where things go

| Path | Purpose |
|---|---|
| `Inbox/` | Temporary material awaiting a decision |
| `Knowledge/` | Durable notes and domain maps |
| `Knowledge/Second Brain Perspective.md` | Only perspective explicitly confirmed by the user |
| `Reviews/` | Reviews of existing knowledge or external artifacts |
| `Decisions/` | Decisions worth preserving with their context |
| `Exports/` | Generated output rather than canonical knowledge |
| `Templates/` | Human and AI note templates |

## Notes and domains

Each durable note should answer one useful question or explain one reusable idea. Its frontmatter contains:

- `type`: `knowledge` for ordinary durable notes;
- `kind`: what the note represents, such as `concept`, `method`, `source`, or `synthesis`;
- `domains`: one or more broad subjects used for retrieval;
- `created`: the creation date.

Domains live in `.codex/skills/knowledge-domains.json`. Each domain has a matching `Knowledge/* Map.md` that explains its scope and links only a few useful entry points. Do not create elaborate taxonomy before real notes require it.

## Sources and perspective

Keep these categories distinct:

- A source claim is what an external source says.
- Synthesis combines or interprets material.
- An AI inference is provisional and must be labeled as such.
- Personal perspective is recorded only after explicit confirmation.

Adding a source means it is useful to retain, not that the user agrees with it. Frequency, links, and note selection do not prove a belief.

## Role boundaries

Use the Expert for factual or conceptual questions and reviews. It starts with the vault, reads the notes that matter, and clearly labels general or live external knowledge.

Use the Interlocutor when the question depends on values, priorities, or tensions. It may use explicitly recorded Perspective but cannot save a new conclusion.

Use the Librarian whenever files should change. It prefers a small update to a suitable existing note over duplication, preserves provenance, and asks before destructive or location-changing operations unless those were explicitly requested.

## Artifact development

For a substantial presentation, article, report, workshop, proposal, or similar artifact, make two separate choices:

- **Role:** use the Expert for neutral, knowledge-grounded work; use the Interlocutor when confirmed Perspective should shape the artifact; use the Librarian only when the result should become durable.
- **Production mode:** choose delegated production, collaborative development, or a mixed mode in which the user retains named choices and delegates bounded activities.

When the mode is materially ambiguous, the Expert or Interlocutor explains what each option means for the concrete task. In collaborative mode, it starts from supplied material, develops consequential choices and sections in reviewable increments, and does not treat sufficient context as permission to complete the artifact. In delegated mode, it clarifies only material gaps and then produces the requested result. Mixed mode can reserve purpose, argument, structure, or voice for the user while delegating research, examples, alternatives, editing, or formatting.

Do not ask about every minor choice or repeatedly reconfirm an unchanged mode. A complete proposal can be used as a provisional thinking instrument when that move is explicit and agreed. Producing an artifact never authorizes saving it; route persistence separately to the Librarian.

## Privacy and backup

Obsidian operates on local files. Hosted AI tools may transmit selected files to a model provider. Git remotes and cloud folders create additional copies. Choose each service deliberately and keep secrets out of the vault.

Git history can retain deleted material. A private remote provides access control, not encryption or a guarantee against accidental sharing. Local-only use with a private backup is fully valid.

## Validation

`scripts/check-vault` runs the mature taxonomy validator and focused tests for validation, retrieval, community analysis, read-only execution, and OpenCode read-only contracts. It checks frontmatter, template contracts, controlled domains, map correspondence, perspective identity, visible links, and completed reviews and decisions. It does not judge truth, writing quality, privacy, or whether a model behaved correctly.

`python3 .codex/skills/retrieve_knowledge.py "query"` returns a bounded local shortlist without contacting a model provider. `scripts/analyze-communities` compares wikilink communities with controlled domains as diagnostic evidence; domains remain human-governed. The guarded `run_read_only_agent.py` launcher additionally requires a Git repository with a commit and an available Codex CLI.
