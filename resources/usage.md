# Skill usage and effects

This is the shared argument and effects reference for Develop, Review, and Research.
Use only methods available in the installed package. Missing methods do not justify
copying a sibling skill, installing tools, or expanding the requested scope.

<a id="notation"></a>
## Requests, values, and context

Slash examples describe requests to the assistant, not Bash commands or a new
executable router. Use the host's supported skill invocation or natural language.
The state helper has a separate terminal CLI, described below.

- `<value>` means a value you supply, not text to type literally.
- `[value]` means the value may be omitted under the resolution rules below.
- Quoted text is a description or question; `--option` names a control outside it.
- Required information need not be repeated when one clear current conversational
  target supplies it. Context supplies information, not permission.

Explicit inputs win over context. Resolve one target before acting. If a target,
business outcome, evidence boundary, or requested effect is ambiguous, ask one
targeted question and stop consequential work. Do not choose arbitrary files,
invent requirements, fuzzily rename a feature, or initialize a misspelled target.

Controls inside a quoted description are data. For example, discussing whether
`--engine debate` should be a default does not select that engine. Parse only
declared controls outside the subject. Unknown values/modes and conflicting
singleton controls produce concise usage, not effects or silently chosen defaults.
Never interpolate a subject, path, or proposed command into an executable shell.

<a id="outcomes"></a>
## Choose the outcome

| Group | Mode | Outcome and required information |
|---|---|---|
| Implementation approach | `develop iterate` | Feedback-driven implementation of an identified feature and outcome. |
| Implementation approach | `develop bdd` | Test-first behavioral implementation; specify observable behavior and preserved contracts. |
| Specification | `develop prd` | Implementation handoff; establish the outcome, baseline, preferred design, and acceptance. |
| Specialized change | `develop prompt` | Edit actual prompts and affected contracts/consumers; establish the requested behavioral delta. |
| Delivery assessment | `develop backlog` | Requirement coverage and ownership from authoritative requirements, tickets, and code evidence. |
| Verification | `develop validate-repo` | Repository checks and local readiness of identified changes, using required project commands. |
| Assessment | `review code` | Implementation review of a declared target/current implementation or real comparison. |
| Assessment | `review smells` | Structural audit of a declared boundary, with complete/partial file coverage and remediation. |
| Decision | `review discuss` | Technical decision with genuine alternatives, evidence, and consequential unknowns. |
| Report maintenance | `research report create|update` | Approved saved evidence and an existing mapped build graph; no new research. |

Mode names select instructions; they are not six equal lifecycles. Prompt rules
specialize the selected executor, while specifications, coverage, and validation
have bounded outcomes. One implementation approach owns sequencing. Reuse adequate
decisions/specifications and existing check evidence instead of repeating a chain.

<a id="defaults"></a>
## Help and omission defaults

```text
/develop help [<mode>]
/review help [<mode>]
```

Help explains outcomes, inputs, defaults, effects, and examples. A bare parent with
no actionable request gives a read-only overview. It does not initialize state,
start implementation, create a demonstration, prepare resources, install anything,
or scan an arbitrary repository. Research's existing report-only selection remains;
link this guide when explaining its usage without conducting research.

For a selected BDD/PRD/prompt/coverage/review method, an omitted subject may come from
one clear current request. If none is established, ask. Output destinations are
separate requests: an illustrative subject such as `import-spec` does not select a
filename. Preserve existing files and announce an appropriate local artifact path
when a requested document is saved. Repository validation's scope is optional;
focused inspection does not replace required full canonical checks.

<a id="iterate"></a>
## Iterate: work, status, and defer

```text
/develop iterate work [--feature <FEATURE_ID>] [--phase <PHASE>]
/develop iterate status [--feature <FEATURE_ID>]
/develop iterate defer "<FOLLOW_UP>" [--feature <FEATURE_ID>] [--kind edge|hardening]
/develop iterate list
```

`FEATURE_ID` is a user-chosen, persistent name, not a built-in feature. The helper
accepts `[A-Za-z0-9][A-Za-z0-9_-]*` and stores `.ai-state/<id>.json` in the target
project. `csv-import` is an example nickname for a hypothetical CSV import; it
does not supply requirements or activate an importer.

| Action | Effect and selection rule |
|---|---|
| Bare Iterate | Read-only status, not automatic continuation. This changes the older default. |
| `status` | Explicit ID, then clear context, then disclosed most-recent selection for viewing only. Recency means file modification time, not conversational focus. |
| `list` | List this project's tracked features and stop; not available skills or tracker tickets. |
| `work` | Resume the selected existing feature. A feature is required information: use a flag or exactly one human-established active target, never recency. |
| `work --phase` | Change that existing feature to an existing phase code, showing old/new stage and skipped prerequisites; this is not acceptance evidence. |
| `defer` | Record a described follow-up against an explicit/human-established ID, then stop. No implementation, tests, or ticket creation. Default kind is `edge`; explicit or clearly identified hardening uses `hardening`. |

Show the selected feature and intended effect before a mutation. Ask only when
uncertain; do not repeatedly confirm an already clear authorized action. New state
requires established start-new intent, ID, and outcome; start in ARCHITECTURE. A
missing resume target is not an initialization request. Missing/corrupt/linked
state is preserved and reported. A new feature cannot jump past establishment.

Status/list with no state report no tracked work; do not turn the helper's no-state
diagnostic into creation. Help requires no helper call merely to explain a term.

### Compatibility and ambiguous names

Unambiguous legacy `<feature> [PHASE]` and `list` remain supported. Legacy `park
"<description>"` maps to defer but may not silently use the most recent feature;
request explicit targeting or use a clear prior human selection.

If `work`, `status`, `defer`, `park`, or `list` could be a feature ID rather than an
action, clarify without writing. `work --feature status` explicitly selects a
feature named `status`. Do not rename files, reserve previously valid IDs, or
silently change an active implementation approach.

<a id="subjects"></a>
## Descriptions are not catalog IDs

| Old example | Meaning; clearer request |
|---|---|
| `reject-duplicate-delivery` | Requested behavior, not a registered scenario. “Reject a repeated delivery without applying its effects twice”; establish duplicate identity and expected effects. |
| `import-spec` | Specification subject, not automatically a path. “Specify the CSV import feature.” |
| `invoice-extraction` | Actual prompt/contract target, not a magic prompt name. “Preserve uncertainty in the invoice extraction prompt”; locate the real editable surfaces. |
| `import-requirements` | Requirements/evidence boundary, not a ticket ID or deferred queue. “Compare import requirements with existing tickets and code.” |

Clear context may supply the subject; otherwise ask for it or the missing source.
Specifications/reviews do not authorize implementing recommendations. Coverage is
not completion or tracker-write authority. Prompt work does not authorize live
model calls or invent missing schemas/replay. Saved-report work still neither
executes notebooks nor acquires evidence.

<a id="review"></a>
## Review: outcome, boundary, input, and engine

```text
/review code [<TARGET>] [--input diff|source] [--engine single|debate]
/review smells [<BOUNDARY>] [--engine single|debate]
/review discuss ["<DECISION_QUESTION>"] [--engine single|debate]
```

| Concept | Meaning |
|---|---|
| Outcome | Implementation acceptability, systematic structural diagnosis, or a technical decision. |
| Target/boundary | What files, subsystem, changes, or question are in scope; establish it explicitly or from unambiguous context. |
| Input | Code review's `diff` comparison versus current `source`. This does not widen finding scope. |
| Engine | Single-pass by default; explicitly selected Debate uses its actual 5→3→1 process and permitted resources. |

`--scope diff|source` is the legacy alias of code review's `--input`. Equal alias
values may normalize; conflicting values stop with usage. Unknown flags/values
do not become subject paths. An explicit diff needs its real base; never invent
one or silently substitute source. Without a control, requested PR/diff/current
changes use their resolved comparison; named current implementations use source.

Implementation review already includes architecture and maintainability. Mentioning
structure does not automatically start a systematic audit. A requested structural
inventory/remediation plan adds that contract and honest file coverage. A decision
question can exist without implemented code; general explanations need no arbitrary
repo scan. `--input` is a code-review control, not an extra discussion/audit flag.

For an explicitly combined implementation review and structural plan, reuse
snapshot-matched source gathering within each reviewer, deduplicate findings, and
include the requested coverage ledger/remediation. Distinguish verified issues,
conditional claims, design choices, and unreviewed files. Supporting callers do
not silently widen findings; a diff sample is not full structural coverage.

Keep original IDs and separate urgency, structural S-levels, and Debate impact.
Independent Debate reviewers may not share initial conclusions. No engine/focus
authorizes editing, posting, installation, or a repeated lifecycle. The alternative
`assess`/`decide` plus `--focus`, mode renames, and `--fix` are not supported.

<a id="phases"></a>
## Checkpoints, not more skills

| Stored phase | User-facing label and completion |
|---|---|
| ARCHITECTURE | Agree direction: outcome/boundaries, unsettled material choices, permitted demo plan, and actual user agreement. |
| HAPPY_PATH | Minimal working flow: deliver the primary outcome while retaining required protections. |
| TEST_BED | Manual demonstration: change representative inputs and observe end-to-end outcomes; report success or a reproducible failure honestly. |
| TWEAKING | Refine with feedback: improve observed behavior until the user accepts it. |
| TESTING | Regression protection: stabilize meaningful automated checks for accepted behavior. |
| FINALIZATION | Agreed follow-ups: brief, address/test or explicitly waive each item; stop before the next item. |

`--phase` is advanced; use existing stored codes, not friendly labels as new values.
Ordinary work follows recorded state without manually choosing a phase. An override
records intent, not proof that a checkpoint passed. Obtain required agreement before
ordinary advancement; preserve explicit jumps and identify skipped prerequisites.

Reuse adequate approved specifications/decisions and confirm current assumptions
rather than recreating an options exercise. Only unsettled material choices need
new comparison. Feedback-driven iteration stabilizes tests after manual feedback;
explicit BDD requires intended behavioral red before production changes. Do not
combine conflicting sequences or claim test-first fidelity from later tests.

<a id="demonstration"></a>
## Manual demonstrations and safety

A test bed is an editable development playground for the feature, not a shipped
skill dashboard, production UI, automated test suite, or model-evaluation pipeline.
Agree the smallest usable surface: existing UI, CLI/sample files, native driver/REPL,
or a thin page. Require both web and Python only when acceptance needs them. The
state helper still needs Python 3.11+; the demo need not be Python.

Keep representative permitted inputs, observable outputs/side effects, reproduction
commands, actual manual feedback, and user edits. Local demos use
`testbed/scratch/<id>`; reusable tools are deliberately promoted to `testbed/tools`.
Do not create generic scaffolding for planning, coverage, review, validation, or
bounded edits. No demo requirement authorizes notebooks, new services/dependencies,
restricted data, provider calls, or deployment contrary to project policy.

Required access, integrity, and resource safeguards precede exposure or consequential
exercise; otherwise contain or block it. Only discretionary completeness is deferred.
Existing checks and necessary safety-contract verification may occur early without
making code-before-test work BDD. Never park an in-scope correctness requirement or
weaken required checks just because it is an edge case.

<a id="helper"></a>
## Separate terminal helper syntax

Resolve Develop's installed `scripts/manifest.py` absolute path and invoke it from
the project being developed. Only use this helper when Develop is actually available.
These terminal commands are separate from the assistant shorthand:

| Action | Existing helper arguments |
|---|---|
| Status | `status [<resolved-id>] -v`; omission is viewing by disclosed recency only. |
| List | `list`; explain a no-state diagnostic without initializing. |
| Defer | `park <resolved-id> <resolved-kind> <description>`; target and kind are positional, not copied skill flags. |
| Work | Read `status <resolved-id> -v`; initialize only established new work with `init <id> --impact <outcome>`. |
| Override | `phase <resolved-id> <PHASE>`, then view status; no automatic acceptance certification. |

The helper's `tool --feature` records who added a tool; it does not select a state
operation target. Test-bed `add` needs `--label` and `--cmd`; `remove` needs an existing
label. Read `--help` and action help for these conditional requirements. All manifest
reads/writes use this CLI; corruption, linked storage, and unknown state are not
permission to reset. Registration is not execution of an external tool.

<a id="rollout"></a>
## Changed defaults and evidence limits

Bare Iterate is now documented as read-only status; legacy parking no longer chooses
recency for a write. Existing unambiguous feature/phase forms and stored data remain;
copied installations keep their old instructions until explicitly upgraded. Do not
update global copies or remove separately installed skills as a usage change.

Product-facing prose can omit internal workflow jargon; skill/workflow manuals must
define it, and state/architecture reports may name stages. A help update does not
authorize implementation, installation, publication, or changes to quality records.

Package/helper/link checks do not prove assistant routing or comprehension. Observed
host/model/user checks need their separately approved scope, settings, data handling,
and budget; unperformed checks remain not-run. See [shared policy](policy.md) and
[selective handoffs](combinations.md). This guide is not a runtime dispatcher.
