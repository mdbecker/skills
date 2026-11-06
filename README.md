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
or a flat multi-agent review. [Usage and effects](resources/usage.md) defines arguments,
context/defaults, state actions, and helper syntax. Slash examples are assistant
requests, not commands to paste into Bash. `/develop help` and `/review help` are
read-only overviews when you need to choose a method.

All modes follow the [shared boundaries](resources/policy.md). A specification,
review, or check does not grant permission to implement, install dependencies, edit
trackers, commit, publish, or deploy. [Adaptation guidance](resources/adaptation.md)
helps map another project's authority, contracts, prerequisites, and commands;
reference profiles are examples, not universal requirements.

## Installation

### Complete bundle

Install every file in a selected exported skill folder, not just `SKILL.md`.
Raw checkout skill folders require preparation and are not portable standalone
installs. Source links use checked-in canonical files; export relocates them to
ordinary package-local resources. Never publish excluded originals to repair links.

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

| Mode | Responsibility and outcome | Guide |
|---|---|---|
| `iterate` | Feedback-driven implementation approach: architecture agreement, a minimal running flow, manual feedback, focused integration tests, and explicitly tracked deferred work. | [Feature lifecycle](develop/iterate.md) |
| `bdd` | Test-first behavioral implementation approach: observable red before production changes, followed by the minimum implementation and verified green. | [Test-first development](develop/bdd.md) |
| `prd` | Implementation specification: one preferred, complete implementation design with contracts, acceptance scenarios, prerequisites, and blocking owner decisions. | [Specification](develop/prd.md) |
| `prompt` | Specialized prompt/contract editing: coordinated generation, wire/schema, validation, application enrichment, accepted replay, consumers, and prompt version/hash changes. | [Prompt contracts](develop/prompt.md) |
| `backlog` | Requirement coverage: an evidence-linked register separating delivery, enabling work, validation, ownership, gaps, and unknowns. | [Requirement coverage](develop/backlog.md) |
| `validate-repo` | Repository checks: the project's required commands, affected-contract evidence, file/staging preservation, failure attribution, and local-readiness report. | [Repository validation](develop/validate-repo.md) |

#### Examples

`csv-import` below is an example feature ID you choose, not a bundled importer.
Establish its actual outcome first. Work resumes/starts that selected feature;
status and list only view state; defer records an explicitly optional follow-up.

```text
/develop iterate work --feature csv-import
/develop iterate status --feature csv-import
/develop iterate defer "Optional import progress display later" --feature csv-import
/develop iterate list
```

For a precisely defined behavior or bounded handoff, describe what you want rather
than copying an unexplained task label. Context may supply an omitted subject;
otherwise the assistant asks for the missing request/source, not an arbitrary ID.

```text
/develop bdd "Reject a repeated delivery without applying its effects twice"
/develop prd "Specify the CSV import feature"
/develop prompt "Preserve uncertainty in invoice extraction and its output contract"
/develop backlog "Compare import requirements with existing tickets and implementation"
/develop validate-repo
```

`import-spec`, `invoice-extraction`, and `import-requirements` were illustrative
subjects, not registered filenames/tickets. Output paths are separate requests.
[Shared usage](resources/usage.md#subjects) distinguishes these argument roles.

#### Boundaries

The iterative approach keeps six [readable checkpoints](resources/usage.md#phases):
agree direction, minimal working flow, manual demonstration, refine with feedback,
regression protection, and agreed follow-ups. Choose an architecture-agreed existing
UI, CLI/sample files, native driver, or thin page; web/Python is not mandatory for
every task. Required protections/checks apply from the start. Local-only work does
not initialize Git or require commits, a remote, or PRs. See the
[complete method](develop/iterate.md).

Bare `/develop iterate` now shows read-only status instead of automatically resuming
recent work. Work/defer need an explicit or human-established ID, not file recency.
Legacy feature/phase and park forms remain when unambiguous, with safer targeting.
Advanced `--phase TWEAKING` means "Refine with feedback" and changes existing state;
it does not prove earlier checkpoints passed. All stored phase codes stay unchanged.

The Python 3.11+ standard-library helper is owned by Develop. Resolve its installed
absolute path and run it from the project being developed, not the skill directory:

```sh
python3 /absolute/path/to/skills/develop/scripts/manifest.py --help
python3 /absolute/path/to/skills/develop/scripts/manifest.py status -v
```

State belongs to the target project's `.ai-state/`; all operations use the installed
helper. Preserve damaged or user-edited state and never reset it to pass checks.
The [complete method](develop/iterate.md) owns tools, storage, phases and recovery.

BDD import/setup errors do not count as behavioral red. Reviewing acceptance
scenarios is read-only. A PRD does not implement its design or bypass architecture
agreement; reuse an adequate approved plan instead of repeating analysis.
Prompt guidance specializes one executor/lifecycle, preserves
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
method. [This repository](resources/profiles/skills.md) supplies its own tooling contract;
the [project mapping](resources/project-profile.md) records the target's current
contracts, runtime, acceptance and permitted effects.

### Review

#### Purpose

Review owns source-grounded assessment, not implementation. Select the assessment
needed for the declared target; general explanations do not require a source audit.
Ordinary review is single-pass.

#### Modes

| Mode | Outcome | Guide |
|---|---|---|
| `code` | Implementation review: findings on intent, architecture, correctness, contracts, compatibility, and maintainability, with evidence and preferred remedies. | [Code review](review/code.md) |
| `smells` | Structural audit: consequence-grounded findings, a file-coverage ledger, and a dependency-aware remediation plan. | [Structural audit](review/smells.md) |
| `discuss` | Technical decision: one supported recommendation with tradeoffs, conditional claims, and consequential unknowns. | [Technical discussion](review/discuss.md) |

#### Examples

`src/importer.py` and `src/importing` are example paths; replace them with accessible
source in the selected project. A diff request needs the actual comparison base.

```text
/review code src/importer.py --input source
/review code "Assess the current changes" --input diff
/review smells src/importing
/review discuss "Synchronous import or queue?" --engine debate
```

#### Boundaries

[Shared usage](resources/usage.md#review) separates the outcome, inspected boundary,
input representation, and engine. `--input diff|source` is canonical for code review;
legacy `--scope` is its alias, not a breadth control. Conflicting values stop with
usage. Literal controls inside a question do not select an engine.

Provide accessible current source, a declared boundary, the real comparison base for
a diff review, and prior findings for re-review. Current-source review without a
base cannot establish when a defect was introduced. Missing sources stay
unreviewed; disclose coverage and checks that were not performed. No findings is
valid, and re-review consolidates prior dispositions rather than appending duplicates.

Code review asks whether the implementation/change is acceptable. A structural
audit diagnoses demonstrated maintenance or behavioral consequences, not file
length or style alone; it does not automatically refactor. Review findings include
locations, evidence or a safe reproduction, impact, urgency, compatibility, and one
preferred complete remedy. Reviews neither apply fixes nor post comments.
Explicit combined implementation/structural requests can reuse snapshot-matched
inspection per reviewer and return one deduplicated report plus requested coverage;
a structural observation alone does not automatically launch another full audit.

Only explicit `--engine debate` selects the [flat voting method](review/debate.md):
three independent peers by default, with private follow-up ballots from those same
peers. Discuss covers every eligible consequential choice; Code/Smells cover
remaining disagreements. `--agents <COUNT>` requires Debate and selects at least
two peers, excluding the coordinator. For example:
`/review discuss "Synchronous import or queue?" --engine debate --agents 5`.
The main agent maps disagreements, verifies evidence, and writes the final report;
it casts a deciding vote only on valid ties. A unique plurality is not a majority,
and abstentions or multiple alternatives can yield ties even with three peers.
Preserve dissent; evidence outranks votes. Three is a practical default, not a
research-established optimum. Scope and single-pass defaults remain unchanged.

The [canonical Debate protocol](review/debate.md) owns packet preparation,
all-option comparisons, validation, recovery and tally rules; read it when selected.
Completed voting is not proof of factual correctness or model quality.

[Model policy](resources/models.md) uses the current model unless an override is
explicitly authorized; there is no model-tier ladder or downstream worker layer.
Batch within actual host/data/tool/budget limits without reducing the selected
count. Missing delegation, evidence, or required submissions remains unavailable
or incomplete, not a simulated complete run. No separate provider CLI, token setup,
or runtime is required. Report available cost honestly, labeling estimates.

The [source-coverage map](review/source-coverage.md) describes the current diagnostic
mechanisms and method boundaries. Detailed checklists, severity distinctions and
worked outputs remain in the selected methods. Findings require evidence from the
actual target and declared scope.

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

`reliability-summary` is an illustrative report subject, not a registered template
or filename. Identify the actual report/project, approved saved inputs, and existing
build mapping before assembly or updates.

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
nor independent review or domain accuracy.

Use the [worked ledger](research/report-worked.md) and
[profile template](research/report-profile.md) alongside the selected methods.
The [fictional reliability-study](resources/profiles/reliability-study.md) example
and [generic project mapping](resources/project-profile.md) demonstrate context,
not universal business or disclosure defaults.

## Combining methods

Each worked example defines its own inputs and acceptance contract. Complete the
target's [project mapping](resources/project-profile.md) before consequential work.
Release artifacts require explicit owner approval and matching verified inputs.

Combine methods only when the next one answers an unresolved question or protects
a specific contract. A sufficient specification can hand off to authorized
development; a changed implementation can hand off to scoped review and validation.
Skip redundant stages and reuse current evidence rather than repeating analysis.
Prompt rules specialize the selected executor; requirement coverage is distinct
from deferred feature work. Existing choices/checks remain inputs, not another
mandatory lifecycle or an approval invented by a handoff.

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
sequences, automatically escalate ordinary review to peer delegation, or add a PRD,
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
.venv/bin/python scripts/validate_skills.py --source --snapshot HEAD
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

The root suite covers manifest/tool-registry behavior, complete exports, scoped
installation/upgrades, corruption/conflict handling, rollback, release contracts,
composition links, and focused workflow/report fixtures. All skill methods and
helpers are tested from their canonical locations. The metadata validator checks
entrypoints, discovery, and complete local/exported resource closure.

Source validation covers every snapshot Markdown file, not only README. It fails
for missing/untracked/ignored targets, including force-added excluded files, before
reading rejected contents. CI uses HEAD; staged preflight uses `--source --snapshot
index`. Working-tree/package observations remain separately labeled. Links/images,
reference forms and HTML navigation are parsed; code/comments are excluded and
external URLs are not fetched. Review public bytes and provenance manually; never
disable privacy exclusions or copy private contents into allowed filenames.

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

Host behavior continues to use manual testing when useful. No automated model
evaluation, formal trial plan, or mandatory per-change host run is required.
Historical model proposals remain reference context; existing release gates are
separate and are not waived or fabricated as passed by deterministic checks.

[Recorded qualification](evaluations/status.json) and the
[evaluation protocol](evaluations/protocol.md) distinguish deterministic results
from host invocation, model behavior, reference fidelity, transfer, and manual
acceptance. Existing installation-layout and documentation evidence does not
certify current live host behavior or this revision's model quality. Release,
model-protocol, and composition-protocol approvals remain separately gated.

Focused evidence lives in [workflow methods](evaluations/workflow-methods/README.md),
[review](evaluations/review/README.md), [repository validation](evaluations/validation/README.md),
and [report maintenance](evaluations/research-report/README.md).
[Discuss ballot scenarios](evaluations/review/discuss-ballots/README.md) cover
decision coverage, packet/comparison quality, recovery and tally boundaries; live
trials remain separately approved and unperformed.
[Usage-workflow scenarios](evaluations/usage-workflows/README.md) separate package/
helper evidence from separately approved assistant/host/user-comprehension trials.
Worked examples are
illustrations, not observed agent outcomes. Frozen inputs/expectations and historical
snapshots retain their identities; evaluator answers are excluded from runtime
bundles. Local deterministic checks do not certify behavioral parity.

Report unavailable task evidence and unperformed checks explicitly.
Approved model access, settings,
data/retention, and budget are required for matched model-mediated comparisons.
Record actual tokens, provider cost, and elapsed time separately; missing metrics
are unavailable, not zero. Any performance tolerance—including the proposed 1.5×
allowance—requires explicit approval and is not unchanged performance.

[Provenance](resources/provenance.json), [NOTICE](NOTICE), and [LICENSE](LICENSE)
record sources, attribution, and licensing.

## Releases

The [usage-contract rollout notes](resources/usage.md#rollout) announce changed bare
Iterate/parking defaults and proportionate demonstrations. They are instruction
changes, not a new runtime router or an automatic upgrade of copied installations.


[Release automation](.github/workflows/release.yml) handles an existing
`vMAJOR.MINOR.PATCH[-prerelease]` tag or manual dispatch. It verifies tag identity
and trusted/default-branch ancestry, runs checks, builds a clean deterministic zip
and checksum, attaches assets to a draft, then publishes. Existing releases/assets
are not overwritten; a failed draft needs explicit maintainer recovery.

Every versioned release requires a clean committed source, explicit owner approval
and a matching source-resource fingerprint. Stable releases additionally require
approved host/model/manual acceptance. An explicit prerelease such as `v0.2.0-rc.1`
may carry honest unverified quality status. Local export does not publish;
creating/pushing a tag or publishing still needs authorization.

## Repository layout

```text
develop/             Development instructions, method documents, and state helper
review/              Review instructions, assessment methods, and flat voting
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
