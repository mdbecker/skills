# Prompt/backlog focused verification

Scope: PRD C and D only. `cases.json` contains independent raw requests/context
and inert local source artifacts. `expected.json` is evaluator-only illustrative
criteria, **not model output or results**. Do not supply it to an evaluated agent.
The worked clinical/municipal/warehouse examples are separately maintained in
the two mode references; held-out museum/freight/campus/course identities do not
reuse them. These files are repository evaluation material, not skill resources.

The parent froze current instructions in `../baseline.json` before these edits.
Preserve that snapshot. Equivalent-input/permission frozen-versus-revised model
comparison is **not performed**: no approved model access/budget/protocol was used.
Deterministic execution below does not substitute for that comparison.

## Case IDs → executable tests

All test names below belong to `tests/test_prompt_backlog_methods.py`.

| Case ID | Test class / method |
|---|---|
| `prompt-museum-issued-processing` | `PromptContractTests.test_heldout_museum_source_exposes_baseline_bug_and_revised_mapping` |
| `prompt-freight-accepted-replay` | `PromptContractTests.test_heldout_freight_filters_failures_repairs_wrong_runs_and_steps` |
| `backlog-campus-complete-coverage` | `BacklogContractTests.test_heldout_campus_source_executes_shared_engine_and_partial_delivery`; `test_heldout_campus_complete_register_matches_roles_priorities_and_gaps`; `test_incomplete_pages_change_unseen_owners_to_unknown_not_gaps` |
| `backlog-course-incomplete-inventory` | `BacklogContractTests.test_heldout_course_source_and_incomplete_register_preserve_unknowns` |

`traceability.json` maps individual supplied requirements to maintained guidance,
worked outputs and real executable tests, including retained/generalized/excluded
dispositions and limitations. Tests execute the Python fences and raw fixture
sources, not just matches against instructional phrases. AST checks restrict
fixture imports and reject executable side-effect boundaries; no source-system,
tracker, provider or model invocation occurs.

## Local execution

```sh
.venv/bin/python -m unittest discover -s tests -p test_prompt_backlog_methods.py -v
```

Actual local result on November 4, 2026: **23 tests passed**, zero failures/errors.
Scoped `git diff --check` passed. Read-only export payload inspection includes all
four assigned references and excludes evaluation material. `results.json` records
these checks; parent final integration/freeze results are separate.

The prompt checks demonstrate strict model wire/final validation, application
identity/time enrichment, report creation versus note service/creation/event time,
nonclinical issuance versus processing, hash/identity/version propagation,
uncertainty in display, and exact-run/step accepted-only replay. Raw baseline
museum and freight sources execute to expose timestamp conflation and failed
payload replay; the worked revised fixture resolves those synthetic consequences.

The backlog checks execute baseline normalization and partial increments, then
reconcile explicit authority/evidence inputs against complete and incomplete pages.
They exercise role separation, semantic existing owners, fractional source versus
tracker priority, validation approval versus implementation, gaps versus unknowns,
overlapping owners and input immutability. They do not infer business authority
or real-world completion from self-reported capabilities.

## Limits

No real application prompt edit, live tracker refresh, production validation,
independent agent artifact, model quality score or model-mediated comparison is
claimed. Contract/example execution and corpus checks establish fixture behavior
only. Source authority/owner judgment and scope/permission adherence still need
approved behavioral evaluation. Parent-owned integration/package results are
reported separately; passing packaging does not establish methodological fidelity.
