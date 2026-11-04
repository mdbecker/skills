# Review source coverage

Maintenance reference for the two supplied review materials, inspected in full
on November 4, 2026. Routine review loads only its selected method, not this map.
This is an instruction-coverage assessment, not evidence of model performance.

## Source identity and interpretation

| Supplied file | SHA-256 | Interpretation |
|---|---|---|
| `code_review.md` | `246c283cd34709915fc74fbe0c8911400b8e36badf1cc65f727f78d30ac979b7` | 66-line review instruction set. Its cleanroom premise applies only when established for the actual target. |
| `code_smell.md` | `1ef0fe6c8593252461516c02ed53401b370719cc4dc0dc4d6bc945899dc7c5a7` | 270-line completed Python review report. Its methodology, reasoning patterns and output structure transfer; its target-specific findings do not. |

Both hashes match the previously pinned `code-review` and `smells` entries in
[provenance](resources/provenance.json). The current inspection extends those
excerpt-only checks to the full supplied files. External prompt-library paths
are not runtime dependencies and the source files themselves are not bundled.

The initial 28-line method references retained the headline boundaries, scales
and concise finding contracts, but compressed away explicit inspection lenses,
remedy decisions, counterexamples and reporting detail. The expanded references
restore those behaviors without making `SKILL.md` a copy of both source files.

## Code-review requirements

Locations refer to the source instruction's lines, not a current code target.
Every row maps to an explicit section of [code review](code.md).

| Source requirement | Source lines | Maintained section / interpretation |
|---|---|---|
| Review the implementation diff associated with the PRD | 1 | Establish the review contract; parent routing distinguishes implementation from PRD design discussion. |
| Ignore environment-only missing hard dependencies | 3 | Establish the review contract; distinguish reviewer setup from a supported production packaging defect. |
| No existing users, backward compatibility or migration constraints | 5 | Choose a decisive, complete remedy; conditional cleanroom policy, not a universal project assumption. |
| Decisive junior-developer handoff, one best solution | 7 | Choose a decisive, complete remedy; concrete ownership/removal/verification, alternatives only for an unresolved real tradeoff. |
| Balance correctness, simplicity, maintainability, project consistency and users/use cases; not the smallest patch | 9 | Choose a decisive, complete remedy; optimize the complete design rather than textual change size. |
| Prefer useful optional cleanup now | 11 | Choose a decisive, complete remedy; cleanroom nits default to recommended now, with a reason for deferral. |
| Intent → architecture → implementation → polish | 13–18 | Review in this order; desirable change before placement, correctness and important nits. |
| Dead, unused or underused code | 22 | Coverage checklist; verify real use, registration and benefit rather than infer deadness from frequency. |
| Unnecessary generalization/specialization and obvious overengineering | 23–24 | Coverage checklist; actual requirements versus speculative or obsolete surfaces. |
| Leaky abstractions | 25 | Coverage checklist; knowledge or repair leaking across boundaries. |
| Risky duplication | 26 | Coverage checklist; algorithms, schema knowledge and policy divergence. |
| Unnecessary complexity | 27 | Coverage checklist; branching, mutable state, modes and indirection. |
| Overly verbose or complex documentation | 28 | Coverage checklist; obscure contracts and synchronization burden without deleting useful depth. |
| Fragile, inconsistent or overengineered tests | 29 | Coverage checklist; behavioral coverage, implementation coupling, setup and redundancy. |
| Cross-file coding and architectural inconsistency | 30 | Coverage checklist; current conventions rather than reviewer taste. |
| Illogical layout or architecture | 31 | Coverage checklist; discoverability and responsibility ownership. |
| Historical names, APIs, boundaries or organization | 32 | Coverage checklist; current intended design and compatibility policy. |
| PRD/implementation/tests/docs inconsistencies | 33 | Review in this order and Coverage checklist; explicit contract alignment. |
| Remove code/tests/docs/config/compatibility branches without users | 34 | Coverage checklist and cleanroom policy; removal recommendation, not edit permission. |
| Too-large, broad or mixed-purpose changes | 35 | Coverage checklist; a coherent split and explicit unreviewed areas. |
| Skip what automation should catch unless tools are missing/misconfigured/inconsistent | 37 | Coverage checklist; report the tooling gap, not a list of automated symptoms. |
| Concrete actionable findings and important nits | 39 | Finding contract; consequence and prescriptive remedy, no finding quota. |
| Four urgency levels and cleanroom fix-now default | 41–48 | Finding contract and cleanroom policy; separate urgency from impact/structural severity. |
| TODO / Question / Follow-up / Nit meanings | 50–55 | Finding contract; preserve type meanings and avoid contradictory urgency labels. |
| Seven per-issue obligations | 57–65 | Finding contract: labels, issue, importance, one fix, balance, timing and effect of no-compatibility assumptions. |
| Combine previous review and new findings into revised output | 66 | Re-review and delivery; consolidated open/resolved/withdrawn/not-reassessed dispositions and duplicate ID aliases. |

## Structural report methodology and findings

Each row maps to [structural audit](smells.md). Historical classes, files and
numbers provide examples only; inspect the current source to justify any finding.

| Source component | Maintained section / behavior |
|---|---|
| Current workspace; all production and repository-support Python; exclusions | Scope and inventory; include relevant CI/support files, distinguish supporting tests from finding scope, honor narrower or non-Python requests. |
| File/line totals and dated locations | Scope and inventory; recompute from the reviewed snapshot and distinguish inventoried from actually inspected files. |
| Concrete maintenance/change-locality/testability/security/operational consequence | Evidence threshold and counterexamples; structural shape alone does not qualify. |
| DTO/protocol/package-marker/adapter/cohesive-routine exceptions | Evidence threshold and counterexamples; useful contracts and boundary work are legitimate designs. |
| S3 correctness/operational; S2 design; S1 maintenance; S0 observation | Findings and severity; not merge urgency or Debate impact. |
| Executive summary recognizes good boundaries and principal pressure points | Report and remediation order; supported context, not a generalized rewrite verdict. |
| F01 multi-reason runner and shared mutable state | Diagnostic families: Large Class / Divergent Change / Solution Sprawl; cohesive collaborators behind a purposeful facade. |
| F02 duplicated validated/unvalidated state machines | Diagnostic families: Duplicated Code / Combinatorial Explosion; one transition loop with narrow policy, not extra boolean modes. |
| F03 repeated primitive event clump and recorder bypass | Diagnostic families: Long Parameter List / Data Clumps / Duplicated Code; event context, one index/serialization/persistence owner and boundary schema. |
| F04 distributed configuration edits across runtime and deployment | Diagnostic families: Shotgun Surgery / Long Method; shared field metadata, scalar parsing versus cross-field invariants. |
| F05 mutable, multi-stage clinical-note budget packaging | Diagnostic families: Long Method / Long Parameter List / Data Clumps; request context, allocator outcomes and payload presentation. |
| F06 evidence parsing/correction/mutation/counters/final-attempt policy | Diagnostic families: Long Method / Conditional Complexity; typed candidates, per-item results and explicit mismatch policy. |
| F07 graph factory, closure state, validation, repair and projection | Diagnostic families: Divergent Change / Long Method; factory seam, dedicated validation/projection and per-run context. |
| F08 raw tool dictionaries coupled to acquisition/guards/presentation | Diagnostic families: Conditional Complexity / Inappropriate Intimacy; stable outcomes, transition policy and separate presentation. |
| F09 row conversion with divergent field/copy/error contracts | Diagnostic families: Oddball Solution / Duplicated Code; one provider-boundary adapter only where contracts match. |
| F10 growing assertion catalog with domain/generic rules mixed | Diagnostic families: Conditional Complexity; typed specs and a small registry only when ownership/variation becomes simpler. |
| Family, locations, evidence, consequence and direction per finding | Findings and severity; add remedy rationale, protected invariants and proposed versus actual validation. |
| Every file mapped to findings or no material finding | Report and remediation order; complete file ledger plus partial/unreviewed states, not an implied perfect codebase. |
| No-finding examples: boundary catches, DTOs, protocols, facades, constants, registry policy and cohesive algorithms | Evidence threshold and counterexamples; inspect real role instead of enforcing a shape rule. |
| Event seam before runner decomposition; independent config; typed pipelines; smaller row/assertion work | Report and remediation order; dependency/risk-based sequencing, not a universal refactoring plan. |

## Deliberate limits

- The separate Python smell guide is still missing. Neither these sources nor
  this update establish coverage of its unknown contents.
- Historical findings, 56-file coverage, 10,012 lines, July 22, 2026 locations,
  class names and facade compatibility choices are not facts or obligations for
  another project. They must not become copied audit results.
- Reviewing these attachments to improve skills does not invoke their embedded
  requests to review/refactor the historical project. Current user intent and
  authority determine the actual task.
- This review-source comparison does not establish completeness of other methods;
  the separate six-method workflow map records the additional supplied context.
- Source mapping, metadata checks and standalone packaging tests do not prove
  that a model follows the restored guidance. Model/host qualification remains
  subject to the existing approved evaluation process.

## Focused PRD coverage

This map also records the focused implementation contract; it does not expand
the work into other skills or certify model behavior.

| Requirement | Maintained guidance / evidence |
|---|---|
| R1: user and agent purpose, triggers, exclusions, inputs, outputs and completion | [Review entrypoint](SKILL.md), Purpose and selection / Inputs and completion; matching Code review or smell audit? section in the repository README. Both methods state their own selection boundary. |
| R2: complete ordered code assessment, decisive remedies, conditional cleanup and consolidated re-review | [Code method](code.md), all sections; original instruction mapping above. |
| R3: ten consequence-grounded diagnostic patterns, counterexamples, S0–S3 and complete audit reporting | [Smell method](smells.md), all sections; F01–F10 and methodology mapping above. |
| R4: read-only work, actual baseline, historical evidence versus current authority and missing guide | [Review entrypoint](SKILL.md) and both methods; Deliberate limits above. |
| Acceptance: standalone method/map resources and focused checks | Explicit review export inventory and standalone packaging tests; package-local links do not require original prompt files. |
| Acceptance: representative findings, compatibility, counterexamples and re-review | Repository-only synthetic cases and evaluator criteria in `evaluations/review/`; `tests/test_review.py` checks their raw-source consequences. These are not agent outputs or runtime dependencies. |
| Acceptance: actual agent adherence | Not run: the existing model-evaluation protocol/access/budget remain unapproved. Source checks and illustrative expected findings do not establish independent agent behavior. |
