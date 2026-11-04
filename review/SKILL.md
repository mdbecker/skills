---
name: review
description: Assess declared code changes or current implementations, audit consequential structural maintenance problems, or discuss technical decisions. Use for requested assessments, not general explanations or implementing fixes. Single-pass unless Debate is explicitly selected.
---

# Review

## Purpose and selection

Choose the assessment the user needs, not every mode that could inspect the code.

| Mode | Use when | Output | Do not use for |
|---|---|---|---|
| `code` | Assessing whether a supplied change or declared current implementation is desirable, correctly placed, correct and maintainable. | Findings with evidence, preferred remedies, urgency, compatibility implications and review coverage. | Implementing fixes or automatically auditing the whole repository. |
| `smells` | Investigating structures that make a declared subsystem or repository harder to maintain, change, test or operate. | Consequence-grounded structural findings, a file coverage ledger and dependency-aware remediation plan. | Size/style criticism alone or automatically performing a refactor. |

For example, `/review code src/importer.py --scope source` assesses the current
importer; `/review smells src/importing` audits that subsystem's structure. A
natural-language request to “review this change for intent, architecture and
correctness” selects `code`; “audit why configuration changes require scattered
edits” selects `smells`. Explicit user intent and current project instructions
govern selection; no slash command is required. A
general question such as "What is a code smell?" needs an explanation, not a
source audit. A request to fix code is implementation, not read-only review;
do not substitute a review or apply a review's recommendations without authority.
Technical decision analysis remains the existing `discuss` mode.

## Inputs and completion

Establish the target, declared scope and accessible current source; read applicable
requirements, instructions, compatibility obligations and relevant supporting
callers/tests/docs. A diff assessment also needs its actual comparison base;
re-review uses supplied prior findings and revisions. Do not invent missing
sources, contracts, consumers or earlier reviews.

Use a clearly established conversational target when no explicit path is supplied.
If the target cannot be resolved, ask one targeted question instead of inspecting
an arbitrary repository. Unavailable sources are unreviewed; disclose partial
coverage and continue only independent, supportable inspection. Lack of a base
can support current-source assessment, not introduced-defect claims.

Finish when the requested report covers the declared scope, supported findings
and remedies, compatibility/uncertainty, prior dispositions when applicable,
and actual versus unperformed checks. No findings is valid. Stop there: do not
invent findings, broaden the audit, refactor, post, or start another workflow.

## Invocation and required methods

For a justified cross-method handoff, read only the relevant [optional recipe](resources/combinations.md).
It grants no edit permission, sibling dependency or automatic Debate selection.

Load [shared boundaries](resources/policy.md), then select one mode:

- `/review code <target> [--scope diff|source] [--engine single|debate]`:
  [code review](code.md).
- `/review smells <scope> [--engine single|debate]`:
  [structural audit](smells.md).
- `/review discuss <topic> [--engine single|debate]`:
  [technical discussion](discuss.md).

Read the selected method in full before reviewing. These references contain the
ordered checks, remedy criteria and output contracts, not optional background.
For maintenance against the original review materials, use the
[source coverage map](source-coverage.md); do not treat historical
findings or assumptions as facts about the current target.

Explicit arguments take precedence. Reject unknown modes, flags or values with
concise usage. Ordinary review defaults to single-pass. A supplied diff/PR uses
its established base; current-source review may proceed without a base, with
that limitation disclosed. Never invent a comparison or expand scope implicitly.
Reviewing PRD design is discussion; reviewing its implementation or the code diff
that implements a PRD is code review. Use the PRD as a contract in that code review,
not as permission to implement it.

Parse scope/engine controls before constructing the review subject. Pass only the
declared target and resolved scope to the canonical Debate method; control flags
are not source paths, shell commands or permission grants.

Scope and execution method are independent. Only explicit Debate selection loads
the [canonical hierarchy](resources/debate/method.md), [model policy](resources/models.md)
and the relevant [Codex](resources/hosts/codex.md) or [Claude](resources/hosts/claude.md)
capability mapping. This is the existing five-reviewer, three-reconciler,
one-synthesizer method, not a new orchestration runtime. Missing resources or
delegation must be reported, not replaced with a claimed completed hierarchy.

Code-review urgency, structural S0–S3 and impact severity are different dimensions.
Do not decide by agreement, invent findings to fill a quota, or call a conditional
claim verified. Inspect raw sources and consequential omissions, preserve minority
findings and unknowns, and report coverage. Use [worked cases](resources/examples.md)
and [adaptation](resources/adaptation.md) only for the chosen scope.

Review remains read-only unless fixes or posting are separately authorized.
Return the requested format, including valid JSON when requested, with actual
evidence, dispositions, preferred remedies or decisions, and unperformed checks.
