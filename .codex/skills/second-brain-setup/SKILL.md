---
name: second-brain-setup
description: Initializes or resumes setup of this Second Brain starter. Use when the user says set up, initialize, onboard, personalize, or help me start this vault. Safely removes synthetic content, creates initial domains and notes, and optionally records explicitly confirmed perspective.
---

# Second Brain Setup

Guide the user to first value without requiring them to understand the system internals. Setup is optional, resumable, and idempotent: inspect current state before every change and never replace user-authored content.

## Setup flow

1. Read `README.md`, `Home.md`, `.codex/skills/knowledge-domains.json`, the titles and frontmatter in `Knowledge/`, and `Knowledge/Second Brain Perspective.md`.
2. Briefly explain the roles: Expert answers read-only, Interlocutor reflects read-only, and Librarian maintains durable files.
3. Identify starter state by content, not by assuming an untouched clone:
   - the synthetic example is removable only while its frontmatter contains `synthetic_example: true`;
   - Perspective is uninitialized only while its frontmatter says `status: uninitialized`;
   - all other Knowledge files are user-owned and must be preserved.
4. Ask whether to keep or remove the synthetic example. If removing it, delete only `Knowledge/Example - Learning Review Cadence.md`, remove only its links from `Home.md`, `Knowledge/Knowledge.md`, and `Knowledge/Knowledge Management Map.md`, and leave the map because it is valid structure.
5. Ask for one broad area the user expects to revisit and one concrete question, source, or idea within it. The user may skip either.
6. If they provide an area:
   - reuse an existing domain when its scope fits;
   - otherwise propose a short lowercase hyphenated domain ID and map title, obtain confirmation, then add both the registry entry and map;
   - avoid building a taxonomy for hypothetical future content.
7. If they provide a concrete item, create one focused note using `Templates/Knowledge note.md`, preserve supplied sources, and link it from the relevant map when it is a useful starting point.
8. Offer an optional Perspective interview. Make clear that skipping leaves all AI roles usable. If accepted, ask at most three focused questions about goals for the vault, relevant priorities or boundaries, and unresolved tensions. Communication or challenge-style preferences belong in conversation instructions, not the canonical Perspective. Show the proposed Perspective wording and require explicit confirmation before replacing the uninitialized state.
9. Update `Home.md` with links to real starting notes. Preserve any user-authored sections and make the smallest edit.
10. Run `scripts/check-vault`, fix setup-caused failures, and finish with one example request for each role.

## Safety rules

- Ask related questions together rather than turning setup into a long wizard.
- Never infer interests, identity, employer, beliefs, or priorities from repository metadata or other files.
- Never delete a note that lacks the exact synthetic marker.
- Never overwrite a domain, map, note, Perspective, or Home content to make setup repeatable.
- If setup is interrupted, leave valid files and resume from observed state next time.
- Do not initialize Git, create a remote, publish content, or change repository visibility. Explain optional private backup instead.
