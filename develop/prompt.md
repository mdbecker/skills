# Targeted prompt and contract editing

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Use this mode for requests such as “change how the model expresses uncertainty”
or “update this prompt and its JSON/replay contract.” Review-only requests remain
read-only. A prompt edit does not select a new development lifecycle, authorize
model calls, or invent an extraction, replay, or evaluation pipeline.

Identify the behavioral delta and actual upstream/downstream surfaces: generation
instructions, schemas/wire examples, validation, replay and versioning. Do not
invent missing extraction or evaluation layers.

## Map ownership before editing

Record the actual files, owners, inputs and consumers for each affected row. Mark
an absent surface not applicable; a missing required contract blocks that part of
the edit rather than justifying a substitute. Keep unaffected surfaces unchanged.

| Surface | Owns / coordinated change | Does not own |
|---|---|---|
| Generation instructions | Desired reasoning/output behavior, uncertainty, source restrictions and exclusions; change the behavioral rule. | Canonical identities, source timestamps, validation success or invented evidence. |
| Model-returned wire hints/examples | Exact model-returned keys, types, enums, null rules and concrete examples; synchronize with the changed rule. | Application-enriched fields or the final persisted shape masquerading as model output. |
| Strict accepted-output validation | Allowed keys/types/values, required fields, source-reference validity, quote rules and cross-field invariants; exercise examples at the real boundary. | Treating valid JSON as accepted output or downgrading rejection to compatibility fallback. |
| Application enrichment and final validation | Resolve supplied identities, verify/reconcile evidence and add authoritative metadata in the established order; validate the enriched output. | Taking identity/time assertions from generated text or silently substituting missing fields. |
| Accepted-output replay | Compact validated results, including new uncertainty/fields needed by later reasoning; consume the established accepted event/output boundary. | Failed JSON, validation errors, repair instructions, full prompts or raw provider responses. |
| Downstream consumers | Read the final validated contract; update rendering/aggregation/export and replay consumers only where the delta affects them. | Inferring occurrence time from an evidence timestamp or converting uncertainty into a positive finding. |
| Logical prompt identity/version/hash | Update the project's registered logical identity/version and hash of the actual model-visible text when that contract exists; verify request metadata matches. | Inventing versioning where none exists, deriving identity from filenames, or leaving stale metadata after model-visible changes. |

Keep generation prompts focused on behavior, wire hints on exact shapes/examples,
and replay summaries on compact validated results. Edit only the affected surfaces
and synchronize their consumers. Preserve authority, uncertainty, redaction,
application-owned fields and accepted-output-only replay where applicable.

For affected acquisition/completeness contracts, map target-defined not-requested,
unavailable, unauthorized, no-match, partial/truncated and execution-failure states,
including source selection, time window and filtering/budget limits. Missing
supplied context is not proof of absent facts. A truncated build log cannot prove
an unseen validation step never ran. Distinguish infrastructure failure from an
authorized empty result; do not add retrieval or a coverage manifest by default.

## Map authoritative metadata, not universal field names

Use the [project mapping](resources/project-profile.md) to identify canonical
source IDs, issuance, receipt, processing and occurrence times. They are different
contracts; never substitute a convenient timestamp or generated identity. Missing
required metadata is a controlled failure under the actual contract, not permission
for a model guess. Keep ownership out of model-facing generation/wire examples.
Inject synthetic application metadata before testing the final strict model only
where the mapped final-output boundary requires it.

Preserve the target's actual null rules, accepted-event selection, enrichment and
reconciliation order, stable resource filenames and logical prompt version/hash.
Do not impose a historical schema, vendor field, journal width, retry count or
quote-matching algorithm. Accepted output can include explicitly unverified evidence
only if the actual contract allows it; acceptance is not adjudicated interpretation.

## Verify and deliver

Add deterministic contract/example regression coverage where supported, respecting
the selected lifecycle's testing stage. Structural validity and generation quality
are different claims; model-backed checks require approved tooling/data/protocol.

Check accepted examples and rejection paths: extra/coerced fields, ambiguous or
unknown evidence references, missing authoritative metadata, forged model-owned
timestamps, and failed/repair-only attempts. Confirm that only accepted outputs
reach replay and downstream consumers, and that metadata reflects every changed
model-visible surface. Preserve the application's existing ordering and safety
boundaries rather than adopting an illustrative fixture as production architecture.

Return coordinated authorized edits, rationale, actual regression evidence and
remaining generation uncertainty. In review-only requests make no edits. Source
`prompt` is recorded in the bundled provenance resources. Read
[the coordinated reference and fictional worked case](prompt-worked.md) when
the mapping or acceptance boundary needs a concrete implementation. The case is
self-contained and uses locally supplied fixture inputs without model calls.
