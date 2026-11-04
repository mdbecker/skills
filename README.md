# Skills

Three project-local skill areas, with two retained compatibility entrypoints:

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

Replace the example paths with your actual checkout and project paths. If a destination already exists, inspect it before replacing it. The links keep installed skills current when you update this checkout.

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

## Combining methods when useful

Use one owning mode when it covers the goal. The [optional cookbook](resources/combinations.md)
describes artifact handoffs, specialization inside one lifecycle, and bounded
feedback—not new commands or automatic multi-agent workflows.

| Remaining problem | Start with |
|---|---|
| Missing delivery or requirement ownership evidence | [C01](resources/combinations.md#c01) |
| An empirical design assumption lacks evidence | [C02](resources/combinations.md#c02) |
| A prompt change affects coordinated consumer contracts | [C03](resources/combinations.md#c03) |
| Demonstrated structural consequences need a remedy | [C04](resources/combinations.md#c04) |
| Saved-evidence report interpretation is disputed | [C05](resources/combinations.md#c05) |
| No additional method would contribute | Stay with the owning mode |

### Delivery coverage: C01

A CSV-import ticket is marked done for queue setup, but user upload/completion is
not evidenced. Reconcile coverage and existing owners; inspect uncertain source
claims only when needed, then specify the missing user-facing increment. Stop at
the authorized handoff rather than invent another queue or edit tracker status.
See [C01's canonical entry, handoff and stop rules](resources/combinations.md#c01).

### Coordinated prompt changes: C03

An invoice consumer treats unknown as zero. Map the affected prompt/wire/validation/
replay surfaces and application-owned fields within the already selected lifecycle.
Prompt guidance specializes the same executor; it does not restart Iterate or
start another editor. Contract checks and generation accuracy remain different.
See [C03's canonical ownership and lifecycle rules](resources/combinations.md#c03).

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
.venv/bin/python -m unittest discover -s iterate/tests -v
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python scripts/validate_skills.py
```

The tests cover manifest behavior. Metadata checks do not prove that models will follow a skill correctly; behavioral changes also need hands-on evaluation.

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
