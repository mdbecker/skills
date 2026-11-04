# Skills

Three independently installable skills for development, review, and research-report
maintenance. Each includes its methods and supporting resources; no sibling skill
installation is required.

## Choose a skill

| Skill | Use it for | Instructions |
|---|---|---|
| `develop` | Implement behavior, write specifications, coordinate prompts, reconcile requirements, or validate repository changes. | [Develop](develop/SKILL.md) |
| `review` | Assess code, diagnose structural problems, or discuss a technical decision without implementing it. | [Review](review/SKILL.md) |
| `research` | Assemble or maintain a report from approved saved evidence through an existing pipeline. | [Research](research/SKILL.md) |

Natural-language requests select the same modes as the command examples below.
Explicit intent and current project instructions govern selection. Use the smallest
applicable method: a simple answer or document edit does not need a feature lifecycle
or a hierarchical review.

All modes follow the [shared boundaries](resources/policy.md). A specification,
review, or check does not grant permission to implement, install dependencies, edit
trackers, commit, publish, or deploy. [Adaptation guidance](resources/adaptation.md)
helps map another project's authority, contracts, prerequisites, and commands;
reference profiles are examples, not universal requirements.

## Installation

### Complete bundle

Download the versioned `skills-<tag>.zip` and companion checksum from a trusted
release, open the target project, and ask its agent to install the skills in the
zip. Use the exported asset, not the automatic GitHub source-code archive.

The archive contains complete selected skills, a manifest, and an auditable
Python 3.11+ standard-library installer. Extracting it does not run code. Inspect
the [installation contract](distribution/README.md) and installer before execution;
internal hashes check integrity, not publisher authenticity. Supply a trusted
external digest with `--sha256` when available.

Required `name` and `description` metadata use the same portable parser during
authoring, export, and installation. Plain strings, quoted strings, inline comments,
and uniformly indented `|`, `|-`, `>`, `>-` blocks are supported. Unsupported
required-field YAML syntax is rejected, not rewritten; source bytes and optional
metadata are preserved. The installer still needs no authoring dependencies.

To build and install a local bundle into another project:

```sh
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python distribution/install.py --archive dist/skills-dev.zip --project /absolute/path/to/target --host codex --dry-run
.venv/bin/python distribution/install.py --archive dist/skills-dev.zip --project /absolute/path/to/target --host codex
```

Codex installs into project `.agents/skills`; Claude Code uses `.claude/skills`
with `--host claude`. Select a subset with `--skills develop review`. Preview first:
identical content is skipped, conflicts and symlink escapes are rejected, and an
explicit `--upgrade` replaces only unchanged, previously managed skill folders.
The receipt and transactional rollback protect existing installations.

The installer does not remove separately installed skills, manage user-global
folders, change hooks/settings/Git state, acquire data, or execute skill workflows.
Do not point it at this checkout's authoring symlinks. Copied installations are
snapshots: updating this repository does not update them; export and explicitly
upgrade the managed project-local copies.

### Live authoring

Clone the repository and complete the [development setup](#development-checks):

```sh
git clone https://github.com/mdbecker/skills.git
cd skills
```

This checkout discovers all three skills through `.agents/skills/`. Prepare their
ignored resource views before use and after changing canonical resources. To use
live-linked authoring in another project, link the prepared skill directories:

```sh
mkdir -p /absolute/path/to/project/.agents/skills
ln -s /absolute/path/to/skills/develop /absolute/path/to/project/.agents/skills/develop
ln -s /absolute/path/to/skills/review /absolute/path/to/project/.agents/skills/review
ln -s /absolute/path/to/skills/research /absolute/path/to/project/.agents/skills/research
```

Replace the example paths and inspect existing destinations before replacing them.
Use complete bundles for portable installation. Use the host's skill picker or
supported invocation syntax; the slash examples describe mode grammar, not proof
of another host's picker or invocation support.

## Skills

### Develop

#### Purpose

Develop owns implementation and its supporting specifications, prompt contracts,
requirement coverage, and repository checks. Ordinary feature development uses the
iterative lifecycle; an explicit test-first request or project requirement selects
BDD. Resolve a conflict with an active lifecycle rather than silently replacing it.

#### Modes

| Mode | Outcome | Guide |
|---|---|---|
| `iterate` | Architecture agreement, a minimal running flow, manual feedback, focused integration tests, and explicitly tracked deferred work. | [Feature lifecycle](develop/iterate.md) |
| `bdd` | Observable behavioral red before production changes, followed by the minimum implementation and verified green. | [Test-first development](develop/bdd.md) |
| `prd` | One preferred, complete implementation design with contracts, acceptance scenarios, prerequisites, and blocking owner decisions. | [Specification](develop/prd.md) |
| `prompt` | Coordinated generation, wire/schema, validation, application enrichment, accepted replay, consumers, and prompt version/hash changes. | [Prompt contracts](develop/prompt.md) |
| `backlog` | An evidence-linked register separating delivery, enabling work, validation, ownership, gaps, and unknowns. | [Requirement coverage](develop/backlog.md) |
| `validate-repo` | The project's required checks, affected-contract evidence, file/staging preservation, failure attribution, and local-readiness report. | [Repository validation](develop/validate-repo.md) |

#### Examples

```text
/develop iterate csv-import
/develop iterate csv-import TWEAKING
/develop iterate park "Reject duplicate deliveries"
/develop iterate list
/develop bdd reject-duplicate-delivery
/develop prd import-spec
/develop prompt invoice-extraction
/develop backlog import-requirements
/develop validate-repo
```

#### Boundaries

The iterative lifecycle retains six phases: architecture, minimal happy path,
manual test bed, tweaking, testing, and finalization. Its test bed includes a basic
web UI and editable Python driver; user feedback precedes stabilized tests and
hardening. It also supports local-only work without initializing Git or requiring
commits, a remote, or PRs. See the [complete method](develop/iterate.md).

The Python 3.11+ standard-library helper is owned by Develop. Resolve its installed
absolute path and run it from the project being developed, not the skill directory:

```sh
python3 /absolute/path/to/skills/develop/scripts/manifest.py --help
python3 /absolute/path/to/skills/develop/scripts/manifest.py status -v
```

State stays in that project's `.ai-state/`. Scratch test beds use `testbed/scratch/`;
reusable tools use `testbed/tools/`. State and registry storage reject symlinks and
escaping paths. Registering an external tool does not execute it. Preserve damaged
state and restore a known-good local copy under user direction; do not hand-edit
or reset it. All feature state changes use the helper.
Nested section types, list entries, and booleans are checked before timestamps or
files change. Duplicate JSON keys and non-JSON values are rejected. Compatible
extra fields and existing optional omissions survive; reads do not backfill files.

BDD import/setup errors do not count as behavioral red. Reviewing acceptance
scenarios is read-only. A PRD does not implement its design or bypass architecture
agreement. Prompt guidance specializes one executor/lifecycle, preserves
application-owned identity and timestamp meaning, and never invents missing
consumers or evidence. Deterministic contract validity is not generation quality.

Requirement coverage is not completion or tracker-write authority, and its register
is separate from the feature's deferred-work queue. Validation does not start a
feature lifecycle or authorize fixes, installation, Git changes, live LLM calls,
or deployment. Inspect command effects before running: formatting, installation,
and build cleanup need applicable permission or an approved isolated run. Focused
green tests never replace full canonical checks; preserve unrelated files/staging
and report patch-related, pre-existing, environmental, or unresolved failures.

Complete [worked cases](resources/examples.md) are linked from each selected
method. [This repository](resources/profiles/skills.md),
[Riskonnect](resources/profiles/riskonnect.md), and the
[agent template](resources/profiles/template.md) provide contextual mappings.

### Review

#### Purpose

Review owns source-grounded assessment, not implementation. Select the assessment
needed for the declared target; general explanations do not require a source audit.
Ordinary review is single-pass.

#### Modes

| Mode | Outcome | Guide |
|---|---|---|
| `code` | Findings on intent, architecture, correctness, contracts, compatibility, and maintainability, with evidence and preferred remedies. | [Code review](review/code.md) |
| `smells` | Consequence-grounded structural findings, a file-coverage ledger, and a dependency-aware remediation plan. | [Structural audit](review/smells.md) |
| `discuss` | One supported technical recommendation with tradeoffs, conditional claims, and consequential unknowns. | [Technical discussion](review/discuss.md) |

#### Examples

```text
/review code src/importer.py --scope source
/review code the current diff --scope diff
/review smells src/importing
/review discuss "Synchronous import or queue?" --engine debate
```

#### Boundaries

Provide accessible current source, a declared scope, the real comparison base for
a diff review, and prior findings for re-review. Current-source review without a
base cannot establish when a defect was introduced. Missing sources stay
unreviewed; disclose coverage and checks that were not performed. No findings is
valid, and re-review consolidates prior dispositions rather than appending duplicates.

Code review asks whether the implementation/change is acceptable. A structural
audit diagnoses demonstrated maintenance or behavioral consequences, not file
length or style alone; it does not automatically refactor. Review findings include
locations, evidence or a safe reproduction, impact, urgency, compatibility, and one
preferred complete remedy. Reviews neither apply fixes nor post comments.

Only explicit `--engine debate` selects the [hierarchical method](review/debate.md):
five independent reviews, three whole-set reconciliations, and one final synthesis.
Preserve dissent and inspect evidence; agreement is not verification. The engine
does not widen the selected source scope and is not a mandatory development gate.

[Model policy](resources/models.md) prefers economical capable reviewers, stronger
reconcilers, and the strongest synthesis within actual host/data/tool/budget limits.
Model identifiers are references, not a whitelist. Same-model distinct agents may
be used when preferred tiers are unavailable, with limits disclosed. Stages still
run in order under observed concurrency. Missing delegation, evidence, or stages
are blockers, not a completed hierarchy; no separate provider CLI, token setup,
or runtime is required. Report available cost honestly, labeling estimates.

The [source-coverage map](review/source-coverage.md) records the supplied historical
materials. Old findings and project assumptions are not current facts; the
separately referenced Python smell guide is unavailable. Detailed checklists,
severity distinctions, and worked outputs remain in the selected methods.

### Research

#### Purpose

Research owns saved-evidence report assembly and maintenance: editorial changes,
chart layout, appendices, diagrams, provenance, and explicitly supported corrections.
Despite its name, it does not conduct new research.

#### Modes

| Mode | Outcome | Guide |
|---|---|---|
| `report create` | Initial assembly from approved saved evidence through an existing mapped build graph. | [Report maintenance](research/report.md) |
| `report update` | Presentation, explanation, or a narrowly supported saved-evidence correction with protected values and meanings. | [Report maintenance](research/report.md) |

#### Examples

```text
/research report create reliability-summary
/research report update reliability-summary
```

“Improve this chart's layout without changing the results” selects report work.
“Correct this count using the supplied corrected aggregate” permits only that
supported correction. “Run another experiment to resolve this discrepancy” is
outside scope.

#### Boundaries

Map authoritative editable inputs, approved saved evidence, dependencies, and the
existing build/check commands. Missing inputs block the affected operation; they
never justify fabricated results or silently omitted sections. Do not acquire data,
execute notebooks, change analytical methods, create a new production pipeline,
fill gaps with model outputs, or publish deliverables.

Preserve claims, source/cohort identities, counts, denominators, selection,
uncertainty, disclosure, and provenance—not merely labels. Cohort counts do not
establish matched samples, pooling legitimacy, scientific validity, or improvement.
Keep reference output aggregate-only: no records, identifiers, sensitive quotes,
credentials, or private coordinates. Failed rebuilding preserves prior outputs
and inputs. Report actual evidence, automated, visual, and offline checks separately
as completed, failed, blocked, or not run; assembly proves neither visual acceptance
nor independent review or clinical accuracy.

Use the [worked ledger](research/report-worked.md) and
[profile template](research/report-profile.md) alongside the selected methods.
The [incidental-findings](resources/profiles/incidental-findings.md) and
[reliability-study](resources/profiles/reliability-study.md) profiles demonstrate
contextual mappings, not universal clinical/privacy defaults.

## Combining methods

Combine methods only when the next one answers an unresolved question or protects
a specific contract. A sufficient specification can hand off to authorized
development; a changed implementation can hand off to scoped review and validation.
Skip redundant stages and reuse current evidence rather than repeating analysis.

| Situation | Useful handoff | Recipe |
|---|---|---|
| Delivery claims do not clearly map to a user outcome | Requirement coverage → optional source review → specification; implementation only when authorized. | [C01: Delivery coverage](resources/combinations.md#c01) |
| A design choice needs representative measurements | Discussion → approved bounded experiment → revisit the affected decision. | [C02: Disagreement to experiment](resources/combinations.md#c02) |
| A prompt change affects consumer contracts | Prompt specialization inside the active lifecycle, with scoped checks as needed. | [C03: Coordinated prompt changes](resources/combinations.md#c03) |
| Duplicated structure has a demonstrated consequence | Structural audit → optional specification → authorized remedy → scoped re-review/validation. | [C04: Refactor with proof](resources/combinations.md#c04) |
| A report interpretation overstates saved evidence | Report maintenance plus optional discussion; report-specific checks remain required. | [C05: Evidence-preserving reports](resources/combinations.md#c05) |

Arrows are possible handoffs, not commands or automatic pipelines. Carry the target
and snapshot, raw evidence, uncertainty, protected contracts, permitted action,
and completion condition. One authorized mode owns the next action; reviewers
recommend and development/report work edits.

Keep one development lifecycle. Do not combine conflicting BDD/iterative test
sequences, automatically escalate ordinary review to nine agents, or add a PRD,
discussion, and audit to every small fix. Another method does not install missing
skills, synchronize state/trackers, acquire evidence, or grant external permissions.
Repository readiness, report acceptance, scientific validity, and live/deployed
verification are different claims. The [cookbook](resources/combinations.md) defines
handoff, skip, stopping, and bounded-recovery rules.

## Development checks

Python 3.11+ is required. Create an environment when needed, then prepare resource
views before testing or validating links:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

The root suite covers manifest/tool-registry behavior, complete exports, scoped
installation/upgrades, corruption/conflict handling, rollback, release contracts,
composition links, and focused workflow/report fixtures. All skill methods and
helpers are tested from their canonical locations. The metadata validator checks
entrypoints, discovery, and complete local/exported resource closure.

Preparation records generated ownership in `dist/.prepared-resources.json` and
uses an exclusive lock. It adopts already matching views, updates unchanged owned
files, and retires only recorded files whose content and mode remain unchanged.
Modified, unknown, linked, or unprovably owned files block preparation without
being deleted. Caches stay unowned. Losing the receipt does not authorize cleanup:
bootstrap matching views before changing canonical resource content, or inspect
conflicts under separate authorization. Interrupted operations restore their own
changes; unsafe rollback preserves competing edits and reports recovery copies.
Staging and no-clobber publication require a filesystem that supports the operation;
there is no fallback to destructive overwriting.

## Evaluation and provenance

[Recorded qualification](evaluations/status.json) and the
[evaluation protocol](evaluations/protocol.md) distinguish deterministic results
from host invocation, model behavior, reference fidelity, transfer, and manual
acceptance. Existing installation-layout and documentation evidence does not
certify current live host behavior or this revision's model quality. Release,
model-protocol, and composition-protocol approvals remain separately gated.

Focused evidence lives in [workflow methods](evaluations/workflow-methods/README.md),
[review](evaluations/review/README.md), [repository validation](evaluations/validation/README.md),
and [report maintenance](evaluations/research-report/README.md). Worked examples are
illustrations, not observed agent outcomes. Frozen inputs/expectations and historical
snapshots retain their identities; evaluator answers are excluded from runtime
bundles. Local deterministic checks do not certify behavioral parity.

Unavailable private historical artifacts, the missing Python smell guide, and
blocked browser inspection remain explicit limits. Approved model access, settings,
data/retention, and budget are required for matched model-mediated comparisons.
Record actual tokens, provider cost, and elapsed time separately; missing metrics
are unavailable, not zero. Any performance tolerance—including the proposed 1.5×
allowance—requires explicit approval and is not unchanged performance.

[Provenance](resources/provenance.json), [NOTICE](NOTICE), and [LICENSE](LICENSE)
record sources, attribution, and licensing.

## Releases

[Release automation](.github/workflows/release.yml) handles an existing
`vMAJOR.MINOR.PATCH[-prerelease]` tag or manual dispatch. It verifies tag identity
and trusted/default-branch ancestry, runs checks, builds a clean deterministic zip
and checksum, attaches assets to a draft, then publishes. Existing releases/assets
are not overwritten; a failed draft needs explicit maintainer recovery.

Stable releases require approved host/model/manual acceptance matching the current
source-resource fingerprint. An explicit prerelease such as `v0.2.0-rc.1` may carry
honest unverified qualification. Local export does not publish; creating/pushing
a tag or publishing still needs authorization.

## Repository layout

```text
develop/             Development instructions, method documents, and state helper
review/              Review instructions, assessment methods, and hierarchy
research/            Saved-evidence report methods, templates, and checks
resources/           Shared policies, host mappings, profiles, examples, provenance
distribution/        Bundle installation contract and scoped installer
evaluations/         Protocols, frozen fixtures, evaluator criteria, recorded limits
tests/               Repository, workflow, manifest, and distribution tests
.agents/skills/      Project-local discovery links for the three skills
scripts/             Explicit exporter and metadata/link validation
.github/workflows/   Continuous validation and authorized release automation
```

[inventory.json](inventory.json) defines package contents. Required method documents,
templates, and worked examples are checked in beside each `SKILL.md`; executable
helpers live in the owning skill's `scripts/`. Local `references/` folders are
ignored and are not runtime, test, or export dependencies.

Per-skill `resources/` and `dist/` are ignored generated views: edit canonical
sources and prepare again, rather than maintaining independent copies. Local
state, scratch test beds, credentials, archives, conversation handoffs, and
`PRD*.md` planning artifacts stay out of commits. See [CONTRIBUTING](CONTRIBUTING.md)
for change and validation guidance and [CI checks](.github/workflows/checks.yml)
for the continuous-validation contract.
