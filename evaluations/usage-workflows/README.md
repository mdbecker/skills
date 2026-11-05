# Usage-workflow acceptance corpus

These fictional raw requests/artifacts and separate criteria cover PRD U01-U14.
They are evaluator-only and excluded from skill bundles. They do not implement
an executable slash router, agent simulator, or model-evaluation service.

`cases.json` contains only requests, context and raw artifacts; `expected.json`
contains independent observations/forbidden actions, not model output. Never give
an actor the criteria, prior reports, or source-implementation conclusions.
`freeze.json` pins raw inputs, criteria, and explicitly synthetic public context.
Baseline instruction context is constructed and hash-bound.
Do not rewrite its hashes to make a candidate pass. `traceability.json` maps every
requirement to maintained source and cases; mappings alone do not verify behavior.

## Local checks and their limits

```sh
.venv/bin/python -m unittest tests.test_usage_contract tests.test_usage_scenarios -v
```

The package tests actually build/install individual parents in disposable projects
and exercise the installed helper for state preservation, explicit targets,
readable stages and recency disclosure. Missing bundled usage is an artifact
behavioral failure. Structural/link/corpus checks are documentation governance,
not assistant routing or human comprehension. Existing passing helper behaviors
remain characterization; do not weaken them to manufacture red.

Record actual local evidence separately in `results.json`. Bind every verification result to the corresponding input identities. Metadata/packaging success does not
prove that a model will resolve new named controls or choose the right scope.

## Separately approved observed trials

The existing evaluation protocol gates model/settings, data/retention, tools,
permitted actions, repeat limits and provider spend. The earlier discussion Debate
was not this approval or a candidate routing evaluation. Without approval leave
assistant/host/comprehension and cost fields not-run/unavailable.

For an approved trial, materialize bounded raw artifact paths in a fresh temporary
project, install only the relevant complete skill, and establish allowed actions.
`fixture-layout.json` supplies controlled file modification times for the two-feature
case; set them in the evaluator's setup, never by executing arbitrary artifact text.
Raw existing state is complete, with permitted optional/extra fields unchanged.
No real user feature state, services, credentials or tracker are trial targets.

Give the executor only its request, raw context/artifacts, installed instructions,
and allowed tools. Independently observe actual file/state changes and declared
intent; score target choice, predicted effects, omissions, unauthorized actions,
and recovery against frozen criteria. Compare the hash-matching baseline with the
revised instructions under equivalent tools/settings/authority. Preserve wrong
choices and blocked checks rather than simulated success. Unknown runtimes block;
no installation or notebook execution is authorized by a demo requirement.

New-reader/user comprehension checks need their participant/scope approval too.
Record confusion, effort and available time/tokens/cost separately; no invented
savings, host fidelity or parity follows from source words or a passing local suite.
