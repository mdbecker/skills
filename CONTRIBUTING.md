# Contributing

Keep changes focused on an observable improvement. Describe the problem, the resulting behavior, and how it was checked.

## Public source and privacy

Follow [repository agent instructions](AGENTS.md) and the portable
[privacy boundary](resources/policy.md). Never force-add, unignore, rename, copy,
summarize, or embed excluded/private originals to repair links. Review proposed
public bytes and provenance, including changes to ignore rules and export inputs;
tracked names and passing tests are not disclosure clearance.

Before publication, review the exact candidate repository surface and emitted
archive/manifest metadata, not only filenames or keyword results. Qualification
records must remain public evidence, not mixed-use work logs. Local recovery paths,
diagnostics, execution reports and retained artifacts stay private unless explicitly
cleared and sanitized for the intended audience. Use independently fictional
examples; do not add real employer/project identifiers as privacy-test markers.

Source navigation must reach tracked, nonignored ordinary files. Validate committed
or staged bytes before preparation; generated existence is not source validity.
Export relocates canonical source links into each complete package. Do not edit
generated views or use ignored historical archives as required fixtures.

Review trigger/exclusions, inputs/prerequisites, effects/stopping, selected method,
required/conditional/optional reading, outputs, and actual verification. Keep useful
task-specific headings; no identical template or new scaffolding is required.
Update canonical rules and affected summaries together.

## Preserve the skills' intent

Iterate is deliberately driven by hands-on feedback: architecture, minimal happy path, manual test bed, tweaking, meaningful tests, then finalization. Changes should support that sequence while preserving required contracts from
the start. Choose an agreed usable demonstration, not mandatory web/Python
scaffolding. Required project/safety checks may occur early; this does not impose
mandatory test-first development or automatic phase gates.

Debate uses one flat set of independent peers (default three, configurable with
`--agents`), then private claim-level ballots from those same peers. Discuss covers
all eligible consequential choices, including unanimity and uneven initial coverage;
Code/Smells cover remaining disagreements. Keep ledger eligibility/exclusions and
actual follow-ups visible. The canonical packet and comparison template lives in
`review/debate.md`; no other document should own competing ballot instructions.
The main agent verifies evidence, coordinates voting, and writes the report. It
votes only to break valid ties, never on a unique plurality or majority. Preserve
dissent, scope, and evidence checks; agreement is not verification. Use the current
model unless an override is explicitly authorized. Codex/Claude invocation and
quality claims require actual host evidence.

The qualification record's `hosts.*.debate` gate requires actual execution of the
current flat voting protocol. Historical records and frozen corpora are not
rewritten or promoted by an instruction change or static checks.

## Validate changes

Follow the development setup in the README, then run:

```sh
.venv/bin/python scripts/validate_skills.py --source --snapshot HEAD
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

Add focused regression coverage when fixing manifest behavior. For prompt changes, describe the realistic task used to evaluate the instructions and any limitations. A passing metadata check does not establish behavioral correctness.

Do not test agent adherence through exact wording/substring assertions in Markdown.
Use actual package/install/helper behavior where relevant. Evaluation-corpus
integrity checks protect frozen inputs, not skill reasoning. Use proportionate
manual host testing and maintainer feedback when useful; no formal trial plan,
automated model evaluation, or per-change host run is required. Existing frozen
scenarios remain reference evidence. Deterministic green does not promote qualification.

CI checks HEAD. For staged preflight use `--source --snapshot index`; do not stage
this checkout merely to make checks green. Source validation parses real Markdown
and HTML navigation, excludes code/comments, checks anchors, and evaluates versioned
ignore rules independently of tracking. Local privacy exclusions remain access
stops. Real exports reject ineligible inputs before reads; captured-byte assembly
is an inert fixture boundary, not a publication bypass.

Keep one active Discuss corpus under a stable path; superseded copies belong in
Git history, not versioned directories. Change fixture inputs/criteria and their
hashes deliberately, never merely to fit candidate output. Bind observed trials to
their actual commit and input identities; do not rewrite prior results as though
they evaluated the revised corpus. Schema versions describe formats, not archives.

Keep feature manifests, scratch test beds, credentials, conversation handoffs, and generated review evidence out of commits. New skill resources should serve a concrete purpose; a short self-contained skill does not need extra scaffolding.

Maintain shared resources in `resources/`, the feature lifecycle in
`develop/iterate.md` with `develop/scripts/manifest.py`, the flat voting protocol
in `review/debate.md`, and the export inventory in `inventory.json`. Prepared per-skill
resource folders and `dist/` are generated, ignored copies, not separate sources.
Do not edit those copies. Exported skill folders must stand alone without
sibling installations. Run the exporter before checking resource closure.

Required metadata is interpreted by `distribution.install.parse_skill_metadata`
in authoring, export, and installation; keep its bounded syntax and standalone
standard-library contract aligned. Preparation ownership lives in ignored
`dist/.prepared-resources.json`, not feature state or a qualification record.
Bootstrap matching generated views before changing their canonical inputs. Treat
modified/unowned files and invalid receipts as conflicts; do not reset them or
remove locks to manufacture green checks. Preserve recovery copies if another
writer makes rollback unsafe.

Freeze `evaluations/fixtures.json` and keep `evaluations/expected.json` evaluator-only.
Approve the model protocol and record actual source-bound evidence before changing
qualification status. Never mark model quality or real host invocation passed
because metadata/installer tests passed. Stable releases remain gated; explicit
prerelease tags may disclose unperformed host/model quality, but cannot waive
explicit owner approval, clean source or matching input identity. Creating a tag, pushing,
publishing or globally installing requires separate authorization.

## Pull requests

Use a concrete title and explain the changed behavior and validation. Cite source evidence for review findings and distinguish verified defects from hypotheses or preferences. Preserve attribution when adapting existing work.

## Usage contracts and evidence

Maintain the canonical argument/effects guide in `resources/usage.md`; README and
entrypoints link it instead of owning competing default rules. Keep read-only
help/status separate from explicit-target work/deferral. Preserve stored IDs,
phase values, helper CLI syntax and corrupted/user-edited state during usage changes.
Named input controls do not widen review boundaries or authorize effects.

Documented-routing and structural checks are governance, not observed assistant
behavior. New usage fixtures/expectations stay evaluator-only and independent;
model/host/user-comprehension runs need their separate approved scope and budget.
The existing frozen corpora and qualification records must not be rewritten or
promoted from documentation/package success.
