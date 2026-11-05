---
name: develop
description: Implement behavior with feedback-driven iteration or requested test-first BDD, write implementation specifications, coordinate prompt contracts, reconcile requirement coverage, or validate repository changes. Select from natural-language intent or explicit modes; review and research reports belong elsewhere.
---

# Develop

Choose the outcome, not every available method. Read [shared boundaries](resources/policy.md)
and the [usage and effects reference](resources/usage.md) when resolving arguments,
help, defaults, or compatibility. The prepared `resources/` directory travels with
this package; do not copy a sibling installation when required resources are missing.

## Outcomes and owning methods

| Mode | Role and outcome | Method |
|---|---|---|
| `iterate` | Feedback-driven implementation with tracked state and manual acceptance. | [Iterative approach](iterate.md) |
| `bdd` | Test-first behavioral implementation: intended red before production changes. | [BDD](bdd.md) |
| `prd` | Implementation specification and preferred developer handoff, not code. | [Specification](prd.md) |
| `prompt` | Specialized prompt/contract editing inside the permitted executor. | [Prompt contracts](prompt.md) |
| `backlog` | Requirement coverage, delivery owners, gaps and unknowns, not the deferred feature queue. | [Coverage](backlog.md) |
| `validate-repo` | Required project checks, preservation, failure attribution and local readiness. | [Repository checks](validate-repo.md) |

Explicit intent and current project policy win. Ordinary feature implementation
uses feedback-driven iteration unless test-first is requested/required. Bounded
edits do not automatically need a full feature lifecycle or demonstration. Resolve
an active-approach conflict rather than silently replacing it. Do not turn planning,
scenario review, coverage, or validation into implementation.

## Inputs, help, and context

Natural language and explicit modes select the same methods. Subjects are meaningful
requests or actual targets, not registered labels such as `import-spec`. An omitted
subject may come from one clear current conversational target; ambiguity needs one
question before consequential work. Context supplies information, not permission.

`/develop help [<mode>]` and a bare parent without an actionable request give a
read-only overview. Help does not initialize feature state, create a test bed,
prepare resources, install tools, or start services. Unknown controls/modes and
conflicting singleton values give usage without effects. Controls inside quoted
subject text remain data. The complete grammar and defaults live in the usage guide.

## Iterate state actions

Use `iterate work`, `status`, `defer`, or `list` with the guide's named controls.
Bare `/develop iterate` is read-only status, replacing the older automatic resume.
Status may disclose most-recent viewing by file modification time. Work/defer require
an explicit or exactly one human-established feature; never select a mutation from
recency. Show the selected ID/effect; ask only when unclear. Missing resume state is
not permission to initialize a misspelling. New work needs ID, outcome, and start-new
intent and begins in ARCHITECTURE.

Unambiguous legacy feature/phase and list forms remain. Legacy park maps to defer
without implicit recent-work writes; clarify IDs that collide with action words.
Existing phase codes, state/history, unknown fields and optional omissions remain.
An override is intent, not proof that prior checkpoints passed.

All actual state operations use this package's `scripts/manifest.py`, resolved by
absolute installed path and invoked from the target project. Skill flags are not
identical to positional helper arguments. Preserve corrupted/linked state; do not
repair or reset it. Read [the full method](iterate.md) before performing work.

## Reuse and stopping boundaries

Reuse adequate approved specifications/discussions as architecture inputs; confirm
remaining assumptions and user agreement without repeating an options exercise.
Prompt guidance specializes one executor, preserving application-owned evidence,
identity/time meaning, validation, accepted replay and versioning. Never invent
missing pipelines or claim generation quality from deterministic contract checks.
Coverage is not completion or tracker authority and does not synchronize feature
state. Feature-state changes require their own explicit or established target.

Validation executes mapped required checks and inspects affected contracts under
permitted command effects. It neither starts a lifecycle nor authorizes fixes,
installation, Git changes, live model calls, or deployment. Record before/after
source and staging, full versus focused checks, failures and omissions. Findings do
not grant implementation permission; focused green never replaces canonical gates.

Read only a useful [optional combination](resources/combinations.md), not a mandatory
chain. Apply [adaptation](resources/adaptation.md) and only the relevant profile:
[this repository](resources/profiles/skills.md) or the
[generic project mapping](resources/project-profile.md) completed from the target's current instructions.
Selected methods link complete [worked cases](resources/examples.md). Return actual
work, checks, evidence and limits; do not claim acceptance or live verification.
