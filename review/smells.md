# Consequence-grounded structural audit

## Contents

- [Scope and inventory](#scope-and-inventory)
- [Evidence threshold and counterexamples](#evidence-threshold-and-counterexamples)
- [Diagnostic families and concrete probes](#diagnostic-families-and-concrete-probes)
- [Remedy design and preserved behavior](#remedy-design-and-preserved-behavior)
- [Findings and severity](#findings-and-severity)
- [Report and remediation order](#report-and-remediation-order)

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](../resources/usage.md).

Audit the declared source for structures that make change, testing, security or
operations materially harder. Inspect actual contracts and consequences; size
alone is not a finding. The [current coverage map](source-coverage.md) records the
maintained diagnostic mechanisms and their evidence requirements.

Load [the worked audit](smells-worked.md) when a complete evidence-to-remedy example
would help: divergent terminal policy, event ownership, scattered configuration,
useful no-findings and incomplete coverage. Its fictional inputs define the task's
contracts and accessible scope.

Use this mode when the requested outcome is structural diagnosis and a maintenance
plan for a declared scope. Assessing whether a particular implementation/change
is acceptable belongs to `code`. A generic question about smells is an explanation,
not authorization to inspect a repository or refactor its code.

## Scope and inventory

- Declare subsystem/repository boundaries, current workspace or commit snapshot,
  language, architecture, public invariants and compatibility requirements.
  Inspect relevant callers, tests and configuration to understand the target.
- For the report-equivalent Python scope, inventory **all production and
  repository-support Python files**, including relevant hidden support directories
  such as CI scripts. Exclude tests, virtual/generated environments and
  non-production experiments from the finding scope unless the user requests them.
  They may still provide supporting evidence; label that distinction. Honor an
  explicitly different scope or language rather than forcing Python defaults.
- Track every eligible file as reviewed, partially reviewed or unreviewed. Calculate
  file/line counts from the actual snapshot if reporting them, explain the counting
  basis, and separate inventory totals from inspected totals. Never reuse the
  any historical file counts, metrics or source locations.
- Inventory responsibility and mutable-state clusters, collaborators, repeated
  algorithms and schema knowledge, and changes requiring coordinated edits. Trace
  actual uses before judging the design; a missing source limits the claim.

## Evidence threshold and counterexamples

A finding needs an identifiable maintenance, change-locality, testability,
security or operational consequence. Explain which change becomes scattered,
which state or policy can diverge, which boundary leaks, or which invariant is at
risk. Size and branch counts can support the explanation but do not prove it.

Do not label DTOs, protocols, package markers, boundary adapters or cohesive long
routines solely because of their size or shape. Check whether a data object names
a real contract, a protocol has useful consumers, a facade preserves a purposeful
public boundary, or a wrapper adds validation/normalization rather than mere
forwarding. Declarative constants and table-driven step definitions can centralize
variation rather than create a smell. Broad catches at CLI/command/logging
boundaries can be proportionate exception translation; inspect their effect, not
just their syntax. Likewise, a lengthy lookup or budget algorithm may be cohesive.

Separate a supported design consequence from a preference and from a direct
correctness defect. State counterevidence and uncertain runtime consequences;
do not elevate "could diverge" to a demonstrated failure without evidence.

## Diagnostic families and concrete probes

Use these diagnostic families where actual consequences support them. Apply those
relevant to the declared scope; there is no requirement to find all ten or introduce
the named design patterns everywhere.

| Family / diagnostic pattern | Inspect and substantiate | Preferred direction when supported |
|---|---|---|
| Bloaters / Large Class; Divergent Change; Couplers / Solution Sprawl (F01) | Unrelated responsibility clusters such as orchestration, retry, tool execution, persistence, failure translation and result construction sharing broad mutable state or collaborators. Show independent reasons to change and focused-test costs. | Keep a purposeful public facade, extracting cohesive collaborators at actual ownership seams rather than splitting by line count. |
| Dispensables / Duplicated Code; Object-Orientation Abusers / Combinatorial Explosion (F02) | Repeated state machines with differing counters, terminal behavior, repairs or validation. Compare transitions and genuinely different completion policies, not just similar loops. | Extract one shared transition loop with a narrow policy/callback and small distinct completion handlers; avoid multiplying boolean modes. |
| Bloaters / Long Parameter List and Data Clumps; Duplicated Code (F03) | Primitive run/step/error/event fields repeatedly forwarded through helpers and serializers, especially a failure path that bypasses the normal recorder. Trace defaults, redaction, indexing and persistence ownership. | Introduce a cohesive event draft/context value and one recorder for index assignment, serialization and persistence; retain the required storage schema at the boundary. |
| Change Preventers / Shotgun Surgery; Long Method (F04) | One setting duplicated across allowed keys, typed settings, precedence, coercion, validation, deployment env names, render arguments and templates. Enumerate the coordinated-edit sites. | Own field/default/env/coercion metadata once and consume it in runtime/deployment paths; separate scalar parsing from cross-field invariants. |
| Bloaters / Long Method, Long Parameter List and Data Clumps (F05) | A packaging routine mixing acquisition, normalization, token estimates, repeated whole-context reconstruction, truncation search, parallel mutable accumulators, metrics and payload presentation. Identify the coupled stages and identity/budget fields. | Use a cohesive request/context value, a budget allocator returning blocks/outcomes, and a separate public payload presenter. Do not fragment a cohesive budget algorithm solely because it is long. |
| Long Method; Object-Orientation Abusers / Conditional Complexity (F06) | A reconciliation pipeline mixing dynamic-shape parsing, source lookup, fuzzy correction, mutation, final-attempt policy, status counters and diagnostics. Trace branches updating the same accumulators. | Parse typed candidates, reconcile each to a result, then reduce results into payload/metadata; make differing mismatch policy explicit rather than a threaded boolean. |
| Divergent Change; Long Method (F07) | Graph construction, nested closures, parse-state history, validation, repair prompts, evidence reconciliation and safe/final result projection sharing a module. Check whether temporary state is per-run or closure-held. | Retain the registry-facing factory where it is a contract; separate validation/reconciliation and projection, with explicit per-run validation context. |
| Conditional Complexity; Couplers / Inappropriate Intimacy (F08) | Orchestration branching on internal tool dictionaries while also owning transitions, retry guidance, templates, events and evidence-source presentation. Look for guards reconstructing argument shapes independently. | Adapt raw tool content once into stable outcome values, isolate the acquisition transition policy, and keep presentation outside it. |
| Dispensables / Oddball Solution and Duplicated Code (F09) | Multiple row adapters using mappings, indexing or `asDict()` with inconsistent copying, required fields and exception contracts. Verify that their domain requirements actually match. | Own one validated row adaptation contract at the storage/provider boundary; let domain mappers consume it without leaking provider-specific shape knowledge. |
| Object-Orientation Abusers / Conditional Complexity (F10) | An expanding assertion catalog requiring fields, validation, branching, result changes and CLI rendering, particularly domain rules mixed with generic checks. | Use typed assertion specifications and a small evaluator registry only when it consolidates real variation; keep domain-specific assertions separate from generic path/equality/list checks. |

One finding may span several families. Name the actual smell and consequence,
not every possible catalog label. These source patterns are not a complete Python
smell guide or exclusive list of problems the current source may exhibit.

## Remedy design and preserved behavior

Recommend one preferred remedy that lowers total complexity and change risk,
not merely the smallest patch or the greatest number of extractions. Typed
values, registries, adapters and state machines must centralize ownership or make
a contract clearer, rather than relocate the same branches behind indirection.
Avoid hypothetical extension mechanisms and additional boolean mode combinations.

Identify the behavior the remedy must preserve: transition and event ordering,
retry/terminal rules, errors and diagnostics, redaction, serialization defaults,
indexes, append-only schemas, configuration precedence/coercion, budget outcomes,
safe outputs, public APIs and security boundaries, as relevant. Preserve known
consumers and compatibility; establish cleanroom only from current target evidence. If
the current task establishes cleanroom, obsolete compatibility surfaces can be
removed, but present behavioral/data/security requirements still apply.

State the behavioral validation needed for those invariants and whether it already
exists, was run or remains proposed. Pure structural changes can use existing
characterization tests; do not manufacture a failing test to justify a refactor.
The audit does not itself authorize tests with external effects or implementation.

## Findings and severity

Each finding includes a stable ID and title, S-level, family/specific smell,
verified current file/line locations, structural evidence, concrete consequence,
one preferred remedy with rationale, protected invariants and needed validation.
When using metrics, derive them from the inspected source. Do not copy historical
IDs, metrics, locations or severity judgments as newly verified findings.

| Structural severity | Meaning |
|---|---|
| S3 | Correctness or operational risk. |
| S2 | Significant design risk. |
| S1 | Maintainability concern. |
| S0 | Observation; distinguish it from actionable defects. |

Keep S0–S3 separate from merge urgency, feedback type and Debate impact labels.
Do not infer one scale from another. Rank findings by supported consequence;
no minimum count or severity distribution is required.

## Report and remediation order

Deliver the requested format; the report-equivalent default includes:

1. **Scope and method:** snapshot, inclusions/exclusions, actual inventory/inspection
   counts when available, evidence sources and missing guide or source limitations.
2. **Executive summary:** useful existing boundaries and the principal structural
   pressure points, not a generic verdict or a claim that everything needs rewriting.
3. **Ranked findings:** the evidence/remedy contract above, with multiple verified
   locations when the consequence crosses files.
4. **File-by-file coverage ledger:** every in-scope file maps to finding IDs,
   "No material finding", partial review or unreviewed with a reason. "No material
   finding" means inspected structure is proportionate to its role, not perfection;
   it cannot describe an unread file. Note useful counterexamples where relevant.
5. **Dependency-aware remediation:** explain which seam reduces risk for later
   changes, then order independent and smaller work. For example, one event
   draft/recorder can precede runner-loop extraction; configuration centralization
   can proceed independently; typed item/acquisition pipelines and smaller row/
   assertion consolidation follow where their dependencies justify it. This is
   a planning example, not a prescribed sequence for every project.
6. **Checks and limits:** actual versus proposed/unperformed validation and
   incomplete inspections. No findings is a valid bounded result.

For a revised audit, reassess prior findings against the new snapshot and retain
their dispositions/IDs without duplicating or silently dropping concerns. Keep
the audit read-only; proposed remediation does not authorize a refactor or posting.
