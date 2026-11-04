# Targeted prompt and contract editing

Identify the behavioral delta and actual upstream/downstream surfaces: generation
instructions, schemas/wire examples, validation, replay and versioning. Do not
invent missing extraction or evaluation layers.

Keep generation prompts focused on behavior, wire hints on exact shapes/examples,
and replay summaries on compact validated results. Edit only the affected surfaces
and synchronize their consumers. Preserve authority, uncertainty, redaction,
application-owned fields and accepted-output-only replay where applicable.

Add deterministic contract/example regression coverage where supported, respecting
the selected lifecycle's testing stage. Structural validity and generation quality
are different claims; model-backed checks require approved tooling/data/protocol.

Return coordinated authorized edits, rationale, actual regression evidence and
remaining generation uncertainty. In review-only requests make no edits. Source
`prompt` and worked cases are in the bundled provenance/examples resources.
