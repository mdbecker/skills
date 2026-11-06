---
name: review
description: Assess implementations, audit consequential structural maintenance problems, or discuss technical decisions. Choose a bounded outcome from natural language or explicit modes; review does not implement fixes. Single-pass unless Debate is explicitly selected.
---

# Review

Read [shared boundaries](resources/policy.md) and the
[usage and effects reference](resources/usage.md) for arguments, help, defaults,
input controls and compatibility. Choose the assessment needed, not every method.

## Outcomes

| Mode | User-facing outcome | Needed evidence and output |
|---|---|---|
| `code` | Implementation review: is this change/current implementation acceptable? | Actual source or real comparison; source-grounded findings, preferred remedies, compatibility and coverage. |
| `smells` | Structural audit: what makes this boundary hard to change or operate? | Declared source inventory; demonstrated consequences, file-coverage ledger and ordered remediation. |
| `discuss` | Technical decision: which direction should we choose? | The actual question, alternatives, constraints and relevant evidence; one supported recommendation and unknowns. |

Code review already covers architecture and maintainability. Mentioning structure
is not automatically a systematic audit. General explanations require neither an
arbitrary repository scan nor a defect quota. Fix requests belong to authorized
Develop work; reviews recommend, not edit. Reviewing a PRD design is discussion;
reviewing its implemented code is implementation review against that contract.

## Subjects, input, help and engine

A target/boundary/topic is required information but may come from one clear current
conversation. Explicit inputs win. If unresolved, ask one targeted question rather
than inventing files, consumers, requirements, comparisons or earlier reports.
`/review help [<mode>]` and a bare parent without an actionable request provide a
read-only overview. Help does not scan a random repository or run a workflow.

Code review's `--input diff|source` selects evidence representation, not inspection
breadth. Legacy `--scope` is its compatibility alias: equal values may normalize;
conflicting values stop with usage. An explicit diff requires its real base; do not
invent one or silently substitute source. Requested PR/diff/current changes use the
resolved comparison; named current implementations use source unless otherwise
specified. Current source without a base cannot establish introduction.

`--engine single|debate` defaults to single-pass. Only explicitly selected Debate
loads [the flat voting protocol](debate.md), [model policy](resources/models.md), and
the relevant [Codex](resources/hosts/codex.md) or [Claude](resources/hosts/claude.md)
capability mapping. Scope and engine are independent. Controls inside a quoted
question are data, not selection or permission. Unknown controls/values produce
usage, not shell execution or subject paths. `--input` is for code review; it is not
an additional audit/discussion flag. Debate-only `--agents <COUNT>` sets at least
two independent peers, default three; the main agent coordinates and writes the
report, voting only to break a valid tie. The usage guide is the grammar authority.

## Required selected methods

- `code`: read [implementation assessment](code.md) in full.
- `smells`: read [structural audit](smells.md) in full.
- `discuss`: read [technical decision](discuss.md) in full.

These are complete procedures, not optional background. For source fidelity use the
[source-coverage map](source-coverage.md); historical assumptions/findings are not
current facts. The package contains its resources without sibling installations;
missing evidence remains unreviewed, not reconstructed by guesswork.

## Combined requests and evidence

For explicitly requested implementation assessment and structural planning, reuse
snapshot-matched source gathering within each reviewer, then produce one deduplicated
report with stable IDs, the requested coverage ledger/remediation, and separate
verified issues, conditional claims, decisions and unknowns. Keep each requested
contract and boundary; a diff sample cannot establish full structural coverage.
Supporting caller/config inspection does not automatically broaden finding scope.

Reuse adequate specifications, prior findings, and checks; revisit only material
new evidence or changed inputs. Re-review consolidates dispositions, retains IDs,
withdraws unsupported claims, and marks unreassessed scope. Do not silently drop
minority findings or require another audit merely for an architectural observation.
Read a relevant [optional recipe](resources/combinations.md) only when useful.

Debate requires the configured independent peers, private ballots from those same
peers on remaining disagreements, and the main agent's final report. The main agent
assigns slightly different facet emphases while explicitly requiring every peer
to assess the full problem. Initial peer conclusions remain isolated. Evidence
outranks votes; preserve supported minority
claims. Missing required submissions remain incomplete, not a single-agent fallback.

## Completion and limits

Stop at the requested report: evidence, preferred remedies/decision, compatibility,
coverage, prior dispositions, and actual versus unperformed checks. No findings is
valid. Keep code-review urgency, structural S0-S3, and Debate impact separate. Do not
post, refactor, initialize state, install tools, delegate ordinary reviews, or start
implementation without explicit authority. Alternative assess/decide/focus grammar,
new installable modes, and a fix shortcut are not supported in this increment.
