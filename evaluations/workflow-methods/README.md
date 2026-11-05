# Six-method verification

The cases exercise develop BDD, PRD, prompt and backlog, plus review code and smells.
Traceability maps each current contract to its worked example and executable check.

## Inputs and observations

Package-local worked documents define complete fictional examples. cases.json,
bdd-prd/ and prompt-backlog/ contain held-out raw tasks, context and inert artifacts;
expected.json contains evaluator-only criteria. Baseline instruction snapshots are
constructed evaluator context with explicit hashes. freeze.json binds the inputs.
Results record actual local observations and separately unperformed checks.

```sh
.venv/bin/python -m unittest tests.test_bdd_prd_methods tests.test_prompt_backlog_methods tests.test_workflow_methods -v
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
.venv/bin/python scripts/check_public_content.py --with-export
```

These execute intended-red/green examples, strict canonical metadata, accepted
replay, recorder/index failure ordering, configuration precedence, scoped review,
coverage roles and fixture identities. Static wording checks are governance;
neither those checks nor worked outputs establish actual assistant behavior.

## Observed actor trials

Use the approved protocol for model/host/data/tools/retention and budgets. Give
an actor only its selected raw request/context, artifacts and permitted tools,
not evaluator answers or peer conclusions. Hold comparison inputs and permissions
fixed; record actual effects, coverage, no-write failures and limits. Missing
prerequisites remain blocked. No additional source acquisition or live-system
operation is implicit.

Project mappings establish target contracts. Examples establish only their own
policies. Model quality, generation, real host invocation, domain validity and
release approval need their own observations. Current methods and worked documents
live beside each SKILL.md; complete resource closures are exported per parent.
