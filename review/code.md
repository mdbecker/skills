# Code review

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Review whether the declared change or current implementation is desirable,
well-placed, correct and maintainable. This is a source-grounded review, not an
automatic repository-wide audit or permission to apply the recommendations.

For a complete ordered review and consolidated revised review, selectively load
[the worked review](code-worked.md). Its supplied snapshots support every location;
its illustrative report is not an observed model evaluation.

Use this mode to decide whether the declared implementation/change is acceptable.
When the requested outcome is instead a structural inventory and remediation
plan for a subsystem, select `smells`; a source sample does not establish a whole
repository review. General code explanations need neither assessment mode.

## Establish the review contract

- Identify the target and actual snapshot: supplied diff/PR and established base,
  or explicitly selected current-source scope. Account for workspace edits when
  those are the target. Without a base, do not claim a defect was introduced by
  an unknown change.
- Read current project instructions, the PRD or other requirements, relevant
  architectural direction and protected contracts. Trace changed code through its
  callers, tests, documentation and configuration as needed to assess consequences;
  distinguish supporting inspection from expanding the finding scope.
- Load available prior findings when re-reviewing. Establish which earlier scope
  and snapshot they described; do not invent a previous review when none is supplied.
- Establish existing users, public consumers and compatibility requirements.
  A historical prompt's pre-user assumption is not evidence about this project.
  If cleanroom/pre-user status is established, apply the cleanup policy below;
  otherwise preserve known contracts and label consequential unknowns.
- Separate failures caused only by the review environment from code defects.
  Missing `pyarrow` or another hard dependency in an atypical environment is not
  itself a finding. An undeclared required production dependency can be a finding
  when supported by packaging and runtime evidence. Disclose checks that could
  not run; continue independent source inspection without pretending they passed.

## Review in this order

1. **Intent:** Does the change solve the right problem? Is the feature, behavior
   or cleanup desirable under the requirements and likely use cases? Identify
   unnecessary or misdirected work before polishing its implementation.
2. **Architecture:** Is responsibility in the right place? Does the design fit the
   current project structure and intended direction, with sensible dependencies,
   APIs and module boundaries?
3. **Implementation:** Is behavior correct, maintainable and reasonably simple?
   Are tests proportionate and meaningful, documentation accurate, and the PRD,
   implementation, tests and docs consistent with one another?
4. **Polish:** Inspect naming, wording, consistency and important nits that improve
   clarity, maintainability or contributor onboarding. Do not let nits displace a
   more consequential intent or design issue.

## Coverage checklist

Use these as inspection lenses, not a finding quota. Substantiate claims with
actual use and a concrete consequence.

| Lens | What to establish |
|---|---|
| Dead, unused or underused code | Callers, registration, supported extension points and whether the remaining benefit justifies the surface. Low usage alone is not proof of dead code. |
| Generalization, specialization and overengineering | Whether abstractions, layers, options or one-off special cases serve real requirements rather than hypothetical users or obsolete designs. |
| Leaky abstractions | Whether callers must know implementation details or repair a boundary's incomplete contract. |
| Risky duplication | Repeated algorithms, schema knowledge, configuration or policies that can diverge; distinguish matching behavior from merely similar syntax. |
| Unnecessary complexity | Branching, modes, mutable state and indirection that make behavior or changes harder to reason about. |
| Documentation complexity | Overly verbose, duplicated or complicated docs that obscure the usable contract or increase synchronization work; retain necessary explanations. |
| Test design | Fragile, inconsistent or overengineered tests, implementation coupling, redundant setup and missing behavioral coverage. |
| Cross-file consistency | Conflicting coding standards or architectural approaches; assess the project's actual conventions rather than personal taste. |
| Layout and ownership | Whether directories, modules and responsibility boundaries are logical, discoverable and easy to follow. |
| Historical names and surfaces | Names, APIs, module boundaries and file organization reflecting former designs instead of today's intended design. |
| Contract alignment | Inconsistencies among the PRD, implementation, tests, docs and configuration, including missing or contradictory acceptance behavior. |
| Removal opportunities | Unnecessary code, tests, docs, configuration, compatibility branches, old references or dead paths; use the established compatibility policy. |
| Reviewability | Changes too large, broad or mixed-purpose to assess effectively. Name the separable concerns and recommend a coherent split; disclose what remains unreviewed. |

Do not spend findings on formatting, routine lint or other issues correctly handled
by automation. Inspect the automation when the diff shows it is missing,
misconfigured or inconsistently applied; report that underlying gap instead of
enumerating every mechanically detectable symptom.

## Choose a decisive, complete remedy

Consider the reasonable solution space, then recommend **one preferred solution**
for each important issue. Balance correctness, simplicity, maintainability,
project consistency and likely users/use cases. The smallest textual patch is
not the objective: prefer the cleanest, clearest, lowest-complexity design that
fully addresses the cause, including relevant tests/docs/configuration.

Make the handoff sufficiently prescriptive for a junior developer: identify what
to remove or move, which boundary should own behavior, what contracts remain,
and how to verify the outcome. Avoid "consider refactoring" without a concrete
direction. Offer alternatives only for a real unresolved tradeoff the available
context cannot settle; explain the decision-changing evidence rather than
leaving an open-ended menu.

When cleanroom/pre-user status and no compatibility obligations are established:

- Do not preserve legacy behavior, old references, dead paths, defensive
  compatibility layers, deprecated APIs or migration mechanisms solely for
  hypothetical existing users. Recommend removing obsolete surfaces rather than
  adding another compatibility wrapper.
- Prefer fixing worthwhile nits and optional cleanup now, especially clarity,
  consistency, maintainability and onboarding improvements. Deferral needs a
  concrete reason such as disproportionate effort or a genuinely separate concern.
- State whether this assumption changes each recommendation. No existing users
  does not erase current behavioral, security, data or architectural requirements.

Outside cleanroom, honor actual consumers and migration obligations. Unknown
compatibility is not removal permission. "Fix now" describes the recommendation,
not authorization for the reviewer to edit code or widen the task.

## Finding contract

Each actionable finding includes:

1. A stable ID, short title, verified file/line location and the actual evidence.
2. **Urgency** and **feedback type**, using the separate scales below.
3. The issue and why it matters: concrete behavioral, maintenance or contributor
   consequence, not a broad stylistic assertion.
4. One preferred complete fix and why it balances simplicity and completeness;
   identify relevant contracts and behavioral validation.
5. Whether it is worth fixing now, with the reason for any deferral.
6. Compatibility assumptions and whether established no-users/no-compatibility
   status changes the fix or its timing.
7. Introduced, worsened or relevant pre-existing status when a real comparison
   supports it; otherwise say introduction is unknown.

| Urgency | Meaning |
|---|---|
| Must fix before merging | A merge blocker supported by the requirements or consequences. |
| Should fix now | Important correction or cleanup that should accompany the change. |
| Optional, but recommended now | Non-blocking improvement worth doing in this revision; default for worthwhile cleanroom nits. |
| Optional, can defer | A justified separate or lower-value improvement; give the reason. |

| Feedback type | Meaning |
|---|---|
| TODO | Must be addressed before merge. |
| Question | Needs an answer, but may not require code changes. |
| Follow-up | Worth considering separately; explain why separation is appropriate. |
| Nit | Small improvement with a clarity, consistency or maintainability benefit. |

Keep urgency separate from impact severity and the structural audit's S0–S3 scale.
Use compatible labels: do not call a deferrable item a mandatory TODO. A question
is for a consequential unknown, not a substitute for making a supported decision.

## Re-review and delivery

Return a consolidated review, not just an appended list of new findings. Recheck
prior claims against current raw evidence: update still-open items, resolve
verified fixes, withdraw stale/unsupported claims with reasons, and merge duplicates
while retaining their IDs as aliases. Add new findings without losing earlier
in-scope concerns. Mark prior items outside the revised scope as not reassessed;
do not silently drop them or call them fixed.

Use the requested output format, including valid JSON when requested, and rank
actionable findings by consequence and urgency. Include scope/snapshot, comparison
limits, reviewed and unreviewed areas, and actual checks with passed/failed/not-run
or blocked status. Do not claim full coverage from a sample. No actionable findings
is a valid result. Do not edit files or post the review without separate authority.
