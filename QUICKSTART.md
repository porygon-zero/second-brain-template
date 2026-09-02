# Quickstart

## 1. Create your vault

Select **Use this template** on GitHub and create a private repository, or download the repository without Git. Open the resulting folder as an Obsidian vault.

Open `Home.md`. Follow the link to the synthetic example to confirm that ordinary Obsidian navigation works.

## 2. Run guided setup

Open OpenCode or Codex with the vault root as its workspace and ask:

> Set up this Second Brain for me. Keep changes minimal and do not infer my interests or beliefs.

The setup skill will:

- explain the three roles;
- ask whether to retain the synthetic example;
- optionally create your first area of knowledge and note;
- offer, but never require, a short Perspective interview;
- update `Home.md`; and
- validate the resulting structure.

You may stop at any question. Running setup again is safe: it inspects the current vault and does not replace user-authored content.

## 3. Get a grounded answer

Ask:

> What does my Second Brain know about learning review cadence?

If you removed the example, substitute the title of your first note. A useful answer names or links the note that informed it and says when the vault has insufficient material.

## 4. Add something useful

Give the Librarian a source or idea:

> Add this to my Second Brain: <URL>

Review the proposed or completed change. The Librarian should preserve the source, distinguish its claims from synthesis, and avoid recording it as your belief.

## 5. Reflect without saving

Ask the Interlocutor:

> Help me think through this decision using my recorded perspective. Do not save anything.

An uninitialized Perspective is valid. In that state, the Interlocutor should ask about relevant values rather than inventing them.

## 6. Check and back up

Run the lightweight structural check after manual changes:

```sh
scripts/check-vault
```

If you use Git, review changes before committing and keep the remote private. Git is optional; another private backup system is also valid.

For local retrieval without an AI provider:

```sh
python3 .codex/skills/retrieve_knowledge.py "learning review cadence"
```
