# Research-report maintenance evaluation

This evaluator-only directory expands the existing synthetic reliability case
into a small saved-evidence report. It is not a research execution tool, production
reporting platform, dependency bundle for the incidental-findings project, or
source of real clinical observations. The four source-project attachments informed
mechanisms only; no source-project file is modified or required at runtime.

## Inputs and independent expectations

`fixtures.py` materializes two isolated fictional target projects: a reference
mapping resembling the existing incidental-findings report profile, and a
nonclinical reliability-study transfer mapping. Each has approved saved aggregates,
an existing tiny assembler/checker, editable chart/presentation sources, a decision
diagram, partial historical archive, supported correction, and failed-build case.
`cases.json` records requests, including applicability and non-activation examples.
`expected.json` fixes evaluator-only results independently of the candidate skill;
`freeze.json` pins the raw corpus and those expectations. Tests must not derive
expected results from the candidate's output or rewrite the freeze to accept a
failure. Intentional corpus changes need an explicit new freeze, not a test repair.

The worked ledger in the runtime skill is a teaching example. Frozen evaluator
answers here are not exported in the skill archive. The helper checks bounded
contracts; it is not a language-model router or an automated scientific reviewer.

## Run and inspect

From the authoring repository, use its existing Python environment:

```sh
.venv/bin/python -m unittest discover -s tests -p test_research_report.py -v
```

Run each fixture in a separate temporary directory. Apply only the requested
presentation change or saved correction through its mapped assembler/checker,
compare protected ledger values AND meanings, and inspect the generated report,
diagram asset/text equivalent, source hashes and check records. Exercise the
failure scenario against an already built report and compare the old bytes after
the failure. No notebooks, queries, model gap-filling or publication are permitted.

For independent forward testing, give an agent the realistic request, current
research skill and raw target artifacts only, not evaluator answers or a suggested
solution. Inspect the agent's actual sources, report and ledger afterwards against
the frozen results. Record who executed what and the resulting artifact hashes;
do not call documentation checks successful agent execution. Such bounded local
tasks do not establish paired baseline performance, another host's behavior,
historical reproducibility or universal parity.

## Verification boundaries

`results.json` records actual completed, failed, blocked and not-run checks, and
`traceability.json` maps PRD requirements to implementation and tests. Test failure
scenarios are expected rejection successes, not fabricated assembly successes.
Static HTML checks cover mapped chart values, nonnumeric cells, anchors, resource
references, SVG and approved embedded scripts/data. Runtime browser controls,
console errors, offline network activity, keyboard, narrow layout and print
readability require actual browser execution/inspection; they are recorded
separately. Assembly alone proves none of those, independent review or science.

Tests mutate protected numerical/semantic fields, suppressed cells, missing
intersections, record-level spatial payloads, external active content, archive
completeness, diagram decisions, staged/live outputs and claimed check statuses.
Only explicitly saved corrections may change their mapped numerical values.
Minimum observations and distinct subjects, permitted fields, rounding and
complement rules are fixture policy, not universal disclosure standards.
