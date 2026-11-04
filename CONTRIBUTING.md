# Contributing

Keep changes focused on an observable improvement. Describe the problem, the resulting behavior, and how it was checked.

## Preserve the skills' intent

Iterate is deliberately driven by hands-on feedback: architecture, minimal happy path, manual test bed, tweaking, meaningful tests, then finalization. Changes should support that sequence. Avoid adding mandatory test-first development, planning artifacts, or automatic phase gates as incidental cleanup.

Debate uses five independent Luna reviewers, three Terra reconciliation passes, and one Astra synthesis. Keep evidence checking separate from agreement, retain dissent when unresolved, and report incomplete coverage honestly. The supported runtime is the Codex skill prompt.

## Validate changes

Follow the development setup in the README, then run:

```sh
.venv/bin/python -m unittest discover -s iterate/tests -v
.venv/bin/python scripts/validate_skills.py
```

Add focused regression coverage when fixing manifest behavior. For prompt changes, describe the realistic task used to evaluate the instructions and any limitations. A passing metadata check does not establish behavioral correctness.

Keep feature manifests, scratch test beds, credentials, conversation handoffs, and generated review evidence out of commits. New skill resources should serve a concrete purpose; a short self-contained skill does not need extra scaffolding.

## Pull requests

Use a concrete title and explain the changed behavior and validation. Cite source evidence for review findings and distinguish verified defects from hypotheses or preferences. Preserve attribution when adapting existing work.
