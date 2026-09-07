# Second Brain Starter

A private-by-default Obsidian vault that an AI can help you build and use.

Your knowledge stays in ordinary Markdown files. Obsidian is the human interface; the included Expert, Interlocutor, and Librarian skills give compatible AI tools clear, separate roles.

## Start in three steps

1. Select **Use this template**, create a **private** repository, and clone it. You can also download the repository if you do not want to use Git.
2. Open the resulting folder as a vault in [Obsidian](https://obsidian.md/).
3. Open OpenCode or Codex in the same folder and ask: **Set up this Second Brain for me.**

The starter already works before setup. Open `Home.md`, browse the synthetic example, or ask the Expert what the vault knows about learning review cadence.

## The three roles

| Role | Use it when | Can change files? |
|---|---|---|
| **Expert** | You want an answer, explanation, comparison, or review grounded in your vault | No |
| **Interlocutor** | You want reflection or challenge shaped by perspective you explicitly recorded | No |
| **Librarian** | You want to add, improve, organize, or remove durable knowledge | Yes, with your authority |

For presentations, articles, reports, and similar artifacts, choose the role and production mode separately. Use the Expert for neutral vault-grounded work or the Interlocutor when confirmed Perspective should shape it. Then choose delegated production, collaborative development, or a mixed mode with named human decisions and bounded AI tasks. The Librarian handles optional persistence.

Example requests:

- `What does my Second Brain know about learning review cadence?`
- `Add this to my Second Brain: <URL>`
- `Help me think through this decision, but do not save anything yet.`
- `Help me develop a presentation from my agenda. Explain collaborative, delegated, and mixed options before drafting.`

## Privacy

The repository contains no personal knowledge from its author. `Knowledge/Example - Learning Review Cadence.md` is synthetic demonstration content, and `Knowledge/Second Brain Perspective.md` starts uninitialized.

Create your instance as a private repository. Local files are not necessarily processed locally: if you use a hosted AI provider, relevant note content may be sent to that provider. Review its privacy and retention terms before adding sensitive, confidential, or employer-owned information.

See [Quickstart](QUICKSTART.md) for the first-use walkthrough and [System Guide](SYSTEM_GUIDE.md) for the complete, compact operating model.

## Requirements

- Obsidian for the intended human experience
- OpenCode or Codex for the optional AI roles
- Python 3.10+ only if you want local retrieval, validation, community analysis, or the guarded Codex launcher
- Git only if you want versioned backup and synchronization

## License

The starter's code, configuration, documentation, templates, and synthetic example are available under the [MIT License](LICENSE). Knowledge added to a template instance belongs to that instance's owner and is not contributed back automatically.
