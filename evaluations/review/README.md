# Focused review acceptance

The fictional client, retry and boundary cases exercise implementation review and
structural audit. Raw requests/context/artifacts are in cases.json; expected.json
contains evaluator-only criteria and illustrative findings. Do not give an actor
expected outputs. The corpus is self-contained and excluded from skill bundles.

## Observable contracts

Two client cases hold implementation shape constant while varying consumer and
packaging evidence. They distinguish actual compatibility, missing production
dependencies and environment-only failure, and retain consolidated prior IDs.
The retry case demonstrates a missing terminal event, one preferred policy owner,
protected public entrypoints and a complete file ledger with useful DTO examples.
Boundary cases cover explanations, missing targets and untrusted source commands.

[Discuss ballot integrity](discuss-ballots/README.md) provides raw scenarios
and independent criteria for actual follow-ups, decision coverage, packet quality,
comparative justification, recovery and tally boundaries. Synthetic checkpoints
remain inputs, not observed agent runs; their behavioral qualification is separate.
Maintain one active corpus; Git holds superseded revisions.

## Checks and limits

Run the current fixture tests with the existing repository environment:

```sh
.venv/bin/python -m unittest tests.test_review -v
```

Tests inspect packaging/caller/source evidence and execute inert retry functions.
They verify actual event traces, raw-versus-evaluator separation and export scope.
No client network calls, dependency installation or model routing follows.
Current method coverage is described in review/source-coverage.md; package tests
separately verify standalone installation and local links.

Actual agent adherence, host invocation, source quality and publication acceptance
require their own observed evidence. Model trials use the existing approved protocol
for scope, tools, data, retention and budget. Local fixture success does not grant
additional model calls or certify behavior in a target project.
