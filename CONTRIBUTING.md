# Contributing

Keep changes focused on an observable improvement. Describe the problem, the resulting behavior, and how it was checked.

## Preserve the skills' intent

Iterate is deliberately driven by hands-on feedback: architecture, minimal happy path, manual test bed, tweaking, meaningful tests, then finalization. Changes should support that sequence. Avoid adding mandatory test-first development, planning artifacts, or automatic phase gates as incidental cleanup.

Debate retains five independent reviews, three independent whole-set reconciliations, and one final synthesis. Model names are reference profiles, not whitelists; prefer economical capable reviewers, stronger middle-stage models and strongest final synthesis within available host/data/budget limits. Preserve dissent, evidence checking and distinct-agent stages independently of model-tier preference. Codex/Claude invocation and quality claims require actual host evidence.

## Validate changes

Follow the development setup in the README, then run:

```sh
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
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
prerelease tags may publish honestly unverified packages. Creating a tag, pushing,
publishing or globally installing requires separate authorization.

## Pull requests

Use a concrete title and explain the changed behavior and validation. Cite source evidence for review findings and distinguish verified defects from hypotheses or preferences. Preserve attribution when adapting existing work.
