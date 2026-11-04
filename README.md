# Skills

Five independently installable skills: three primary areas and two retained
compatibility entrypoints. This README covers the skills maintained in this
repository, not unrelated host-bundled or plugin skills.

- **`/develop`** — Iterate or explicit BDD, specifications, prompt changes, requirement coverage, and repository validation.
- **`/review`** — Code/current-source review, structural audit, or technical discussion; single-pass unless Debate is explicitly selected.
- **`/research report create|update`** — Saved-evidence assembly and maintenance through an existing report pipeline; not new research.
- **`/iterate`** and **`/debate`** retain their arguments and canonical methods as compatibility entrypoints.

Each exported folder contains its full resources without sibling installations.
Debate is optional, not an Iterate gate. Model references are not a whitelist;
prefer economical capable reviewers, stronger middle-stage models and strongest
final synthesis within available host/data/tool/budget permissions.

Installation/metadata checks do not certify host invocation or model quality.
See `evaluations/status.json` for unperformed gates; full acceptance is not claimed.

## Skill catalog

[`inventory.json`](inventory.json) defines the exported skills, methods and shared
resources. All five are discoverable through this checkout's `.agents/skills/`
links; each can also be installed on its own from a complete exported bundle.

| Skill | Available modes | Canonical instructions |
|---|---|---|
| `develop` | `iterate`, `bdd`, `prd`, `prompt`, `backlog`, `validate-repo` | [Develop](develop/SKILL.md) |
| `review` | `code`, `smells`, `discuss`; `single` or explicit `debate` engine | [Review](review/SKILL.md) |
| `research` | `report create`, `report update` | [Research reports](research/SKILL.md) |
| `iterate` | Feature creation/resumption, phase selection, `park`, `list` | [Iterate](iterate/SKILL.md) |
| `debate` | Explicit hierarchical `review` or `discuss` | [Debate](debate/SKILL.md) |

Develop includes the canonical Iterate method and helper; Review includes the
canonical Debate method. Installing either parent does not require installing
its compatibility entrypoint. Shared policies, host mappings, project profiles,
worked examples and composition guidance travel with every exported skill.

## Which skill should I use?

Choose by the outcome you need next, not by how many skills are installed. These
skills add working discipline: development controls how a change is made, review
challenges evidence and decisions without editing, and report work protects claims
while assembling saved results. They are not five steps that every task must follow.

For new work, start with `develop`, `review` or `research`. Use `iterate` and
`debate` directly when you want their existing standalone entrypoints; they do not
add capabilities missing from the corresponding parents.

| What you need now | Choose | Why and when it helps | Expected result |
|---|---|---|---|
| Build a feature whose behavior or ergonomics needs hands-on feedback | `/develop iterate <feature>` or `/iterate <feature>` | You need to agree on architecture, try a minimal end-to-end flow and refine it before stabilizing tests. This is the default feature-development lifecycle. | An implemented flow, a manual test bed, integration tests and explicitly tracked deferred work, with user checkpoints. |
| Fix or add precisely specified behavior using test-first development | `/develop bdd <task>` | You can describe an observable acceptance outcome, or the project explicitly requires red-before-code. A duplicate-delivery bug is a typical case. | A genuine failing behavioral test, the minimum implementation and a verified green result. |
| Decide what an implementer should build, without building it yet | `/develop prd <target>` | The desired outcome exists, but contracts, compatibility, failure behavior or acceptance criteria need a complete developer handoff. | A preferred design and implementation specification with bounded unresolved decisions. |
| Change a generation prompt without breaking its consumers | `/develop prompt <target>` | Prompt meaning also appears in schemas, examples, validation or replay; changing wording alone could leave those surfaces inconsistent. | Coordinated authorized prompt/contract edits, checked within the chosen lifecycle. |
| Find out whether requirements are actually delivered and owned | `/develop backlog <scope>` | Tickets, enabling infrastructure and user-visible completion do not clearly line up. Use it before inventing more work or duplicate owners. | An evidence-linked coverage register separating delivered, partial, missing and unknown work. |
| Check whether a repository change is locally ready | `/develop validate-repo [scope]` | You need the project's actual tests/checks, prerequisites and final-change inspection, rather than another design opinion. | Check results, failures and blockers; not a deployment or permission to fix everything. |
| Look for actionable defects in a change or current source | `/review code <target>` | You want an independent source-grounded assessment of correctness, compatibility and implementation choices before accepting or revising code. | Findings with evidence, preferred remedies, urgency and coverage; no edits. |
| Understand why a subsystem is difficult or risky to change | `/review smells <scope>` | Repeated policies, coupled state or scattered responsibilities have a concrete maintenance or behavioral consequence. Use an explicit structural scope, not a file-length quota. | Consequence-grounded structural findings and a dependency-aware remedy plan; no refactoring. |
| Choose between technical alternatives | `/review discuss <topic>` | You need to challenge a decision such as synchronous versus queued import, compare real tradeoffs and identify evidence that could change the recommendation. | A supported preferred decision, conditional claims and consequential unknowns; no implementation. |
| Assemble or revise a report from results you already have | `/research report create|update <target>` | Approved saved evidence and an existing report build pipeline are available, and claims, provenance, uncertainty or privacy must survive the edits. | A built/updated report with actual evidence and acceptance-check status; no new research. |
| Explicitly request independent challenge and reconciliation | Add `--engine debate` to a review mode, or use `/debate review|discuss ...` | A consequential decision or disputed finding warrants the additional nine-agent process and its resource cost. This is optional, not the default for ordinary review. | Five independent reviews, three whole-set reconciliations and one evidence-checked synthesis, subject to actual host capability. |

If you only need a simple answer or a small document edit, a full development
lifecycle or hierarchical review may add nothing. Use the smallest applicable
method, and stop when the requested answer or authorized handoff is complete.

### Where the purposes overlap

- **Develop and Iterate:** `/develop iterate` uses the same canonical lifecycle as
  `/iterate`, including phase selection, `park` and `list`. Choose one entrypoint;
  do not run both as separate workflows for the same feature. Develop additionally
  exposes specification, BDD, prompt, coverage and validation modes.
- **Review and Debate:** Debate is an execution engine for explicitly selected
  review/discussion, not another kind of implementation work. Review defaults to
  single-pass and adds scope/engine controls. Do not run a completed Debate again
  through the other entrypoint just to get a second version of the same analysis.
- **Iterate and BDD:** both implement and verify behavior, but their sequencing
  differs. Iterate refines behavior through manual feedback before its testing
  phase; BDD demonstrates behavioral red before production changes. Select one
  lifecycle, not both. Given/When/Then wording does not turn Iterate into BDD.
- **PRD, architecture and discussion:** all can compare designs. Discussion owns
  the decision analysis; PRD owns a complete implementation handoff; Iterate's
  architecture phase owns direction and user agreement for an active feature.
  Reuse settled evidence instead of repeating all three. A PRD does not bypass
  Iterate's architecture checkpoint.
- **Code review and structural audit:** both inspect source and may notice the
  same duplicated policy. Code review asks whether the implementation/change is
  acceptable; a smell audit asks which structural consequences make the declared
  scope risky to maintain. A code review does not automatically become a broader
  audit, and an audit does not automatically authorize a refactor.
- **Review and repository validation:** review supplies reasoned findings;
  validation supplies results from mapped project checks and readiness inspection.
  They complement each other, but passing tests does not settle every design claim
  and a persuasive review does not mean checks ran.
- **Requirement coverage and Iterate's deferred work:** `develop backlog` maps
  requirements to delivery evidence and owners. Iterate's local queue tracks
  concerns deferred within a feature. Neither is a replacement for the other;
  they are not automatically synchronized.
- **Prompt editing and development:** prompt guidance specializes affected
  contracts inside the same authorized executor and lifecycle. It is not a second
  feature workflow, and contract tests do not prove generation accuracy.
- **Research reports and discussion/validation:** report work owns evidence,
  provenance, report edits and report acceptance. Discussion can challenge an
  interpretation; repository validation can check changed supporting code. Neither
  supplies missing evidence or replaces report-specific checks. Despite its name,
  `research` does not conduct new research or build a new report pipeline.

## Current qualification

The recorded status in [`evaluations/status.json`](evaluations/status.json) is:

- Deterministic checks, temporary Codex/Claude layout installation and composition
  documentation/packaging checks: passed.
- Real host installation/discovery, invocation and hierarchy checks: not run.
- Manual acceptance, model quality, reference fidelity, transfer and composition
  model behavior: not run.
- Release, model-protocol and composition-protocol approval: pending.

Recorded limits include unavailable private historical artifacts and the separately
referenced Python smell guide, plus blocked browser visual inspection. These records
are not proof of current live host behavior. Stable release readiness also requires
acceptance evidence matching the current source-resource fingerprint.

## Install

### Another project: use the zip

Download a versioned skill zip and its checksum from a trusted release, open your
target project and ask its agent: **“install the skills in this zip file.”**
Choose `skills-<tag>.zip`, not GitHub's automatic source-code archive. The
archive's root README and manifest describe scoped installation and include an
auditable Python 3.11+ standard-library installer. Extracting a zip never autoruns
code. The agent must inspect it and retain applicable approvals.

The installer copies complete selected folders into project `.agents/skills`
for Codex or `.claude/skills` for Claude Code. It previews changes, skips identical
content, rejects conflicts/symlink escapes, and upgrades only unchanged previously
managed files when requested. No global install, hooks, settings edits, Git changes,
data acquisition or skill-workflow execution occurs.

For a local bundle from this checkout, prepare/export first, then use the audited
source installer against a different project:

```sh
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python distribution/install.py --archive dist/skills-dev.zip --project /absolute/path/to/target --host codex --dry-run
.venv/bin/python distribution/install.py --archive dist/skills-dev.zip --project /absolute/path/to/target --host codex
```

Use `--host claude`, `--skills develop review`, or explicitly requested `--upgrade`
as appropriate. Do not point the copy installer at this checkout's authoring
symlinks. Internal hashes check integrity, not publisher authenticity; supply the
trusted external digest with `--sha256` when available.

### Local authoring

Clone the repository:

```sh
git clone https://github.com/mdbecker/skills.git
cd skills
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/build_skills.py --prepare
```

This checkout includes all five discovery links in `.agents/skills/`. Prepare the
ignored resource closures before local use. For live-linked authoring elsewhere,
link the prepared directories; portable distribution should use the zip instead:

```sh
mkdir -p /absolute/path/to/your-project/.agents/skills
ln -s /absolute/path/to/skills/develop /absolute/path/to/your-project/.agents/skills/develop
ln -s /absolute/path/to/skills/review /absolute/path/to/your-project/.agents/skills/review
ln -s /absolute/path/to/skills/research /absolute/path/to/your-project/.agents/skills/research
ln -s /absolute/path/to/skills/iterate /absolute/path/to/your-project/.agents/skills/iterate
ln -s /absolute/path/to/skills/debate /absolute/path/to/your-project/.agents/skills/debate
```

Replace the example paths with your actual checkout and project paths. If a
destination already exists, inspect it before replacing it. The links keep source
instructions current when you update this checkout; run
`scripts/build_skills.py --prepare` again to refresh their generated resources.
Copied installations are snapshots: pulling this repository does not update them.
Use the inspected bundle's installer and explicitly requested `--upgrade` for
previously managed project-local copies. The zip installer does not manage or
update user-global skill folders.

Use your skill picker or the host's supported invocation syntax. Slash examples
describe mode grammar; `$`/picker presentation does not itself certify another host.

## Area commands

```text
/develop iterate csv-import
/develop bdd reject-duplicate-delivery
/develop prd import-spec
/develop prompt invoice-extraction
/develop backlog import-requirements
/develop validate-repo
/review code src/importer.py --scope source
/review smells src/importer
/review discuss "Synchronous import or queue?" --engine debate
/research report create reliability-summary
/research report update reliability-summary
```

Explicit BDD is genuinely test-first; ordinary Iterate keeps manual feedback before
its testing stage. Drafting/review does not implement changes. Coverage registers
are separate from Iterate state. Current-source review needs no invented baseline;
changing review engine does not widen scope. Reports require saved evidence and
a mapped existing build graph; missing dependencies block work.

### Mode boundaries

- [`bdd`](develop/references/bdd.md) observes a genuine behavioral red test before
  implementing the minimum change and verifying green; import/setup failures do not
  count as red. It does not silently replace an active Iterate lifecycle.
- [`prd`](develop/references/prd.md) produces a preferred implementation design,
  contracts, acceptance scenarios and bounded unknowns, not implementation.
- [`prompt`](develop/references/prompt.md) coordinates affected generation, schema,
  validation and replay surfaces within the selected lifecycle. Deterministic
  contract validity does not establish generation quality.
- [`backlog`](develop/references/backlog.md) maps requirements, owners, implementation
  evidence and gaps in a separate coverage register; it is read-only by default and
  does not synchronize Iterate state or automatically edit trackers.
- [`validate-repo`](develop/references/validate-repo.md) checks the declared scope
  against existing project commands. Readiness inspection does not authorize fixes,
  dependency installation, formatting or live/deployed verification.
- [`code`](review/references/code.md), [`smells`](review/references/smells.md) and
  [`discuss`](review/references/discuss.md) inspect defects, consequential structure
  or a technical decision respectively. They do not implement fixes or post reviews.
- [`report create|update`](research/references/report.md) edits authoritative report
  inputs using approved saved evidence and an existing build pipeline; it does not
  acquire evidence, execute notebooks, invent results or publish deliverables.

Shared [boundaries](resources/policy.md) apply throughout. Use
[adaptation guidance](resources/adaptation.md) to map a different project's
instructions, protected contracts, permissions, prerequisites and checks; bundled
profiles are examples, not assumptions about an uninspected project.

## Combining methods when useful

Combine methods only when the second one answers a question the first does not.
Usually this means passing a finding, specification or observation to the next
authorized action, not running multiple skills concurrently. The
[optional cookbook](resources/combinations.md) gives detailed handoff, skip and
stop rules; these are not new commands or automatic pipelines.

| Situation | Useful combination | What each contributes; when to skip a step |
|---|---|---|
| A feature needs a clear handoff before implementation | `develop prd` → `develop iterate` | PRD settles the implementation contract; Iterate builds and refines it with the user. Skip a separate PRD if the existing brief is adequate. Implementation needs its own authorization and architecture agreement. |
| A change needs independent assessment and local readiness evidence | Chosen development mode → `review code` → `develop validate-repo` | Development edits; review challenges the actual change; validation runs mapped checks. Add review only for a useful requested/necessary assessment, and reuse current check evidence rather than rerunning unchanged work. |
| A ticket is done, but the user journey may be missing | `develop backlog` → optional `review code` → `develop prd`; then authorized Iterate and validation if needed | Coverage separates enabling work from delivery; source review resolves uncertain claims; PRD specifies the missing increment. Skip source review when evidence already suffices. Coverage-only or planning work stops before implementation. [C01](resources/combinations.md#c01) |
| A design choice depends on measurements you do not yet have | `review discuss` → bounded experiment brief → authorized Iterate test bed → revisit the affected decision/specification | Discussion identifies a discriminating observation; the approved experiment supplies actual evidence. Skip the experiment if existing measurements settle the question. Do not call a provisional experiment a settled production design or ship it implicitly. [C02](resources/combinations.md#c02) |
| An invoice prompt change could turn unknown into zero downstream | `develop prompt` within the active Iterate or explicitly selected BDD lifecycle; optional scoped review/validation | Prompt guidance maps field meaning and consumers; the same lifecycle/executor owns edits and testing order. Use prompt alone for a bounded wording edit; do not start both lifecycles or invent missing consumers. [C03](resources/combinations.md#c03) |
| Duplicated policies have a demonstrated failure or maintenance consequence | `review smells` → optional PRD → authorized development → scoped re-review/validation | Audit establishes the consequence; development applies the smallest complete remedy; follow-up checks test that concern. Skip PRD when the remedy is clear. Behavioral fixes can use explicit BDD; pure refactors can reuse green characterization without manufacturing red. [C04](resources/combinations.md#c04) |
| A report headline overstates what saved cohorts support | `research report create|update` + optional `review discuss`; repository validation only for affected supporting code | Report mode owns evidence, protected claims and edits; discussion tests the disputed interpretation against the same saved sources. Skip discussion when report evidence already resolves it. Neither validation nor discussion replaces visual/evidence checks or authorizes new data. [C05](resources/combinations.md#c05) |

Arrows describe possible handoffs, not permission to execute the whole chain.
Carry the target/snapshot, actual evidence, uncertainties, protected contracts,
permitted action and completion condition into the next step. Recheck consequential
claims against raw sources; reviewer agreement is not evidence.

Keep one development lifecycle and one owner of the next action. Reviewers recommend;
authorized development or report work edits. An optional second method does not
create another manifest, install missing skills, edit trackers, publish, deploy or
launch Debate. Choose `--engine debate` explicitly only when that additional
independent challenge is warranted and available.

### Combinations to avoid

- `/iterate` followed by `/develop iterate` for the same feature: two entrypoints,
  one method, not two complementary stages.
- BDD alongside Iterate to get both test sequences: conflicting lifecycle timing,
  not additional coverage. Preserve the active lifecycle unless a change is agreed.
- Ordinary review followed automatically by Debate: more agents are not a mandatory
  acceptance gate. Revisit only material new evidence or an explicitly selected need.
- PRD plus discussion plus a smell audit for every small fix: reuse a clear contract
  and remedy instead of producing redundant analysis.
- `research` to fill an evidence gap in a design experiment or report: this skill
  works with approved saved results, not data acquisition or invented measurements.
- `validate-repo` as proof a report is scientifically valid or a feature is deployed:
  repository readiness, report acceptance and live verification are different claims.

## Iterate

```text
/iterate csv-import
/iterate csv-import TWEAKING
/iterate park "Reject duplicate deliveries"
/iterate list
```

Iterate follows six phases:

1. **ARCHITECTURE:** record the impact, exclusions, data flow, and real design tradeoffs; agree on direction with the user.
2. **HAPPY_PATH:** implement the smallest useful flow and park additional concerns.
3. **TEST_BED:** provide a basic web UI and an editable Python driver, run the flow, and hand it to the user.
4. **TWEAKING:** change, run, observe, and repeat until the user says the behavior feels right.
5. **TESTING:** add a few meaningful integration tests for the stabilized flow.
6. **FINALIZATION:** address or explicitly waive deferred work one item at a time.

The bundled manifest helper requires **Python 3.11+** and uses only the standard library. Run it from the project being developed, using the installed helper's absolute path:

```sh
python3 /absolute/path/to/skills/iterate/manifest.py --help
python3 /absolute/path/to/skills/iterate/manifest.py status -v
```

State lives in that project's `.ai-state/` directory. It stays local and supports later-session resumption. The state directory and manifest files must not be symlinks. Feature-specific test-bed files stay in `testbed/scratch/`; reusable tools can be promoted to `testbed/tools/`.

The tool registry rejects linked or escaping storage at `testbed/tools/registry.json`,
including ancestor and leaf links. Explicit external tool references can still be
registered without executing them. Damaged feature state is preserved; restore a
known-good local copy under user direction rather than hand-editing or resetting it.

Git projects can use phase commits and small PRs. Local-only projects retain the same six phases and feedback checkpoints without requiring Git, a remote, or PRs. See [the full Iterate instructions](iterate/SKILL.md).

## Debate

```text
/debate review the current implementation and its diff against main
/debate review src/importer.py and its integration tests
/debate discuss "Should this import run synchronously or as a job?"
```

Debate uses actual host delegation and model availability. These are reference
selections, not required IDs or physical-size classifications:

| Stage | Agents | Reference / available alternative | Responsibility |
|---|---:|---|---|
| Independent review | 5 | `gpt-6-luna` | Complementary independent evidence inspection |
| Reconciliation | 3 | `gpt-6.1-terra` / `gpt-6.1-sol` | Each checks every candidate, counterevidence and omissions |
| Final synthesis | 1 | `gpt-6-astra` | Verify supported findings and produce the final response |

Stages run in order under observed concurrency. Same-model distinct agents are
permitted when preferred tiers are unavailable; disclose tier uncertainty instead
of falsely claiming XL qualification. Substitutions inside approved boundaries
need no repetitive model-ID approval. Missing required delegation/evidence or
incomplete stages remain blockers. No provider CLI, token setup or new runtime.

Findings must include source locations, concrete evidence or a safe reproduction, impact, severity, and the smallest reasonable fix. Agreement between reviewers is not verification. Reports distinguish verified defects, conditional claims, preferences, unresolved disagreements, and coverage limits. Cost information is reported only when available, with estimates labeled as estimates.

Reviews do not authorize code changes or publishing comments. See [the full Debate instructions](debate/SKILL.md).

## Development checks

Python 3.11+ is required. Create a development environment and run:

```sh
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s iterate/tests -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

The Iterate suite covers manifest and tool-registry behavior. The root suite covers
distribution, release contracts and composition guidance. Prepare resource closures
before running those suites, especially after changes to canonical resources.
Metadata checks do not prove that models will follow a skill correctly; behavioral
changes also need hands-on evaluation.

Distribution tests additionally exercise deterministic exports, installation,
standalone helpers, conflicts, upgrades, archive validation and rollback. The
protocol, evaluator-only fixtures/answers, source matrix and acceptance limits are
under `evaluations/`. Real Codex/Claude invocation and paired quality/cost checks
require their own approved evidence; they are not simulated by installer tests.

Composition checks additionally install each parent/legacy package alone in both
host layouts, verify canonical guide/anchor closure and validate frozen evaluator
criteria. They do not simulate agent route selection or certify model behavior.

## Releases

The release workflow handles an existing `vMAJOR.MINOR.PATCH[-prerelease]` tag or
manual dispatch. It verifies tagged/default-branch ancestry, runs canonical checks,
builds a clean deterministic zip/checksum, attaches assets to a draft, then publishes.
It refuses to overwrite existing releases/assets; a failed draft requires an
explicit maintainer recovery decision. No release is created by local builds.

Stable export/publication remains blocked until reviewed model/host acceptance and
approval records pass and match the current source-resource fingerprint. A tag
such as `v0.2.0-rc.1` explicitly produces a prerelease with honest qualification
metadata. Creating/pushing any tag or publishing still requires authorization.

The installation contract is in `distribution/README.md`; release automation is
defined in `.github/workflows/release.yml`. Runtime archives exclude evaluation answers,
local state, environments, credentials and restricted data.

## Layout

```text
iterate/             Development skill, manifest helper, and regression tests
debate/              Prompt-only hierarchical review skill
develop/             Development area and focused method references
review/              Single-pass scopes and explicit Debate selection
research/            Saved-evidence report assembly and maintenance
resources/           Canonical common policies, profiles, examples and provenance
distribution/        Archive README and scoped installer
evaluations/         Protocol, synthetic fixtures, evaluator answers and limits
tests/               Distribution and release-contract tests
.agents/skills/      Project-local discovery links
scripts/             Explicit resource exporter and metadata/link checks
.github/workflows/   Automated validation
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for change guidelines, [NOTICE](NOTICE) for provenance, and [LICENSE](LICENSE) for the MIT license.

Generated per-skill `resources/` and `dist/` are ignored export views; edit their
canonical sources, then prepare again. No source/helper logic is independently
maintained in those copies.

`inventory.json` controls package contents. `.github/workflows/checks.yml` runs
continuous validation; `.github/workflows/release.yml` handles authorized releases.
The `PRD*.md` files are design/acceptance references, not substitutes for current
skill instructions or recorded qualification evidence.
