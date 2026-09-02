# Knowledge model, epistemics, and source honesty

Load this reference when interpreting metadata, sources, beliefs, provenance, or the Perspective.

## Retrieval metadata

- `kind` identifies what a note represents; `domains` identify subjects to which it materially contributes.
- Treat `.codex/skills/knowledge-domains.json` as the controlled domain registry and map routing table. Domain membership supports discovery; it implies neither relevance to a query nor endorsement.
- Follow meaningful semantic relationships only when they can supply a premise, caveat, disagreement, application, or provenance needed for the answer.

## Stance

Treat `stance` as categorical, never as a strength score:

- `adopted`: explicit user commitment.
- `aligned`: compatible with recorded personal perspective without proving commitment.
- `exploring`: under consideration.
- `contested`: material disagreement or unresolved conflict.
- `reference`: useful context without a position.

Stance never overrides content and never licenses an inference about belief.

## Epistemic categories

Keep these categories distinct and surface them when material:

1. **Explicit personal perspective:** directly confirmed under `## Explicit personal commitments` or clearly attributed to the user elsewhere.
2. **Exploring position:** a possibility the user has not adopted.
3. **Vault position:** a stable synthesis supported across relevant notes.
4. **Source claim:** attributable to a cited author or reference.
5. **Derived view:** a new synthesis or inference produced from the corpus.
6. **External supplement:** information obtained outside the vault.

`[[Second Brain Perspective]]` contains explicit, exploring, and derived layers. Do not flatten them into one belief system or use its interlocutor character; conversational character belongs to `second-brain-interlocutor`.

## Source verification

`source_checked: YYYY-MM-DD` records a historical check of cited claims. It proves neither authority, present currentness, nor fitness for a decision. Never imply an external source was opened when only its vault note was read.

For legal, regulatory, financial, safety-critical, operational, price, current-product, or otherwise consequential use, verify live against official or primary authorities and original publications. State jurisdiction and an `as of` date when applicable. Disclose inaccessible material and visible-scope limitations; abstracts, excerpts, and previews support only what they expose.
