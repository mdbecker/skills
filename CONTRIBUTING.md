# Contributing

Keep changes focused on an observable improvement. Describe the problem, the resulting behavior, and how it was checked.

## Preserve the skills' intent

Iterate is deliberately driven by hands-on feedback: architecture, minimal happy path, manual test bed, tweaking, meaningful tests, then finalization. Changes should support that sequence while preserving required contracts from
the start. Choose an agreed usable demonstration, not mandatory web/Python
scaffolding. Required project/safety checks may occur early; this does not impose
mandatory test-first development or automatic phase gates.

Debate retains five independent reviews, three independent whole-set reconciliations, and one final synthesis. Model names are reference profiles, not whitelists; prefer economical capable reviewers, stronger middle-stage models and strongest final synthesis within available host/data/budget limits. Preserve dissent, evidence checking and distinct-agent stages independently of model-tier preference. Codex/Claude invocation and quality claims require actual host evidence.

## Validate changes

Follow the development setup in the README, then run:

```sh
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
.venv/bin/python scripts/check_public_content.py --with-export
```

Add focused regression coverage when fixing manifest behavior. For prompt changes, describe the realistic task used to evaluate the instructions and any limitations. A passing metadata check does not establish behavioral correctness.

Keep feature manifests, scratch test beds, credentials, conversation handoffs, and generated review evidence out of commits. New skill resources should serve a concrete purpose; a short self-contained skill does not need extra scaffolding.

Maintain shared resources in `resources/`, the feature lifecycle in
`develop/iterate.md` with `develop/scripts/manifest.py`, the review hierarchy
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
content, private-marker, semantic, rights or history review. Creating a tag, pushing,
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
