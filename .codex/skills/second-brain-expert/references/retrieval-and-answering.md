# Retrieval, answering, and knowledge-grounded writing

Load this reference before consulting the vault or producing an answer or draft from it.

## Workflow

1. Frame the topic, desired judgment, audience, and output. Ask only when ambiguity would materially change the result.
2. For a narrow question, search the exact requested concept before broadening. Use the quoted phrase, known or likely aliases and expansions, and likely definitional forms such as `"<concept> is"`, `"<concept> means"`, or domain-appropriate equivalents. When a term is ambiguous or compositional, search the whole phrase and its concept-specific paraphrases; a match for one generic constituent does not establish coverage of the requested concept. Use direct links, focused file/content search, or, when helpful, `python3 <vault>/.codex/skills/retrieve_knowledge.py "<query>"`. The helper ranks titles, aliases, summaries, and domains first, then unions low-weight matches from visible full-note prose; comments and code do not contribute. It is optional acceleration, not a gate to vault knowledge. Treat its default results as an initial shortlist, not a context limit; rerun focused queries, increase `--limit`, or use other retrieval paths when coverage is incomplete. Treat scores as candidate-selection rationale, not evidence.
3. For a broad question, use the relevant registry definition plus the concise summary and selected entry points in its domain guide. For a genuine cross-domain question, orient from each relevant guide without treating either as a complete context packet.
4. Read as many promising substantive notes fully as the task requires. Categorize candidates internally as **incidental** when they only share words or examples, **contextual** when they provide relevant background without entailing the central claim, or **material** when an exact passage explicitly defines or asserts the claim or supplies sufficient premises for it. Continue until the material concepts, explicitly named frameworks or sources, counterarguments, qualifications, and provenance are adequately covered. Prefer relevance over an arbitrary note count, while avoiding retrieval that cannot affect the answer.
5. Follow semantic links only when they can change or qualify the conclusion. Do not traverse links merely because they exist.
6. Test whether the selected notes contain enough depth for the requested judgment. If they are relevant but lack necessary review criteria, examples, evidence, or authoritative detail, do not stop at the vault summary: follow cited provenance to original sources and consult additional authoritative or primary sources when needed. For code and requirements reviews, keep repository-specific specifications, architecture, conventions, and tests authoritative about intended behavior; use external sources to supply evaluation criteria or technical facts, not to invent replacement requirements. Also consult source notes and external sources when provenance, disagreement, freshness, or consequence requires it.
7. Draft the proposed lead claim. As a final preflight, identify the exact sentence or passage and note that entails it. Shared terminology, topical proximity, domain metadata, or a passage about a neighboring concept does not pass. If the mapping cannot be made, classify the result as no material vault knowledge and use the mandatory disclosure. Otherwise lead with the conclusion, show the strongest reasoning, include material alternatives and tensions, and cite only notes that affected the answer.

## No-result fallback

When retrieval and focused search find no note and exact passage that materially entail the proposed lead claim of a factual or conceptual answer, make the response's first sentence exactly: “No material vault knowledge was found for this question; the following is a general-knowledge answer.” This is a default-fail gate: incidental or contextual notes do not suppress the disclosure, even if they use nearby terminology. Continue with general knowledge when it can answer the question safely. Label live research as an external supplement and cite it normally. Do not add irrelevant vault citations merely to make an answer appear grounded.

## Knowledge-grounded writing

- For substantial artifact development, follow the shared `../../artifact-development.md` protocol before drafting.
- Infer or ask for audience, intended effect, genre, and constraints.
- Preserve the epistemic category of every consequential claim.
- Adapt vocabulary and abstraction without simplifying by omission.
- Use a neutral authorial voice unless the user supplies another voice explicitly; never borrow the Interlocutor character implicitly.
- Do not write in the user's first-person moral voice from aligned, exploring, selected, or derived material. Use first-person personal commitments only when the scope is explicitly recorded or freshly confirmed.
- Make persuasion inspectable: do not let polish substitute for evidence or suppress credible alternatives.

## Reporting

State vault limitations, external supplements, and currentness checks when material. For a read-only vault audit, report findings without repairing files.
