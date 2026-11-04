# Repository validation acceptance

This extension qualifies only `/develop validate-repo`. It does not certify other
methods, real host invocation, live agents, live LLM evals or deployed workloads.
The [qualification record](qualification.json) distinguishes actual evidence from
unperformed behavior. [Traceability](traceability.json) maps the validation PRD.

## Frozen inputs and isolated execution

Keep the existing `validation-reference`, `validation-transfer`,
`untrusted-command` and five `validate-repository-changes-*` boundary cases in the
root evaluation corpus unchanged. Its pre-extension hashes are recorded in
[baseline.md](baseline.md); those snapshots must not be rewritten to fit a result.

The new [cases](cases.json) and evaluator-only [expected outcomes](expected.json)
are frozen in [freeze.json](freeze.json) before their first execution. The
[fixture materializer](fixtures.py) creates disposable repositories with real
behavioral tests, tracked history and deliberately mixed dirty/index state. It
does not edit or run the original Databricks project. Use only synthetic local
inputs; no downloads, installs, real secrets, Databricks access or live services.
Missing runtimes are blocked, not substituted with a fake passing test.

Required substantive cases:

| Case | Observations required |
|---|---|
| Documented contract regression | Baseline behavior passes; the candidate's documented table-storage contract fails when missing Spark silently invokes a local fallback reader instead of raising. This synthetic contract test is not a run of the original template's persistence tests. |
| Focused green, canonical red | Focused tests really pass while required full canonical validation really fails; no local-ready claim or replacement of the full gate. |
| Genuinely pre-existing failure | The same behavioral failure is observed on the identified baseline and candidate with the same command and suitable equivalent environment; attribution is not based on guesswork. |
| Authorized formatting and mixed edits | Formatter really changes permitted formatting; unrelated staged/unstaged content and mixed edits remain intact, with the index preserved and after-state evidence. |
| Staged artifacts and sensitive configuration | Staged synthetic build/config findings are identified without printing sensitive values, deleting files or unstaging user content, even if tests pass. |
| Non-Python behavioral transfer | The other project's real JavaScript behavioral test fails under its own canonical tooling, without Python/pre-commit/Spark requirements being imposed. |

Run the deterministic fixture/evaluator tests from this repository root:

```sh
.venv/bin/python -m unittest discover -s tests -p test_validation.py -v
.venv/bin/python -m evaluations.validation.evaluator --output /tmp/validation-evidence.json
```

These tests exercise the repositories, failures and evaluator counterexamples.
They do **not** simulate successful agent behavior or performance qualification.
They are evaluation helpers, not a new production validation engine or skill.

The runner exposes `fixtures.materialize`, `snapshot`, `record`, and
`trusted_records`; `Fixture.actor_context()` returns only the raw request, project
root and command/runtime mapping. `evaluator.evaluate` compares controlled
receipts and independent current file/index observations; `exercise` and the CLI
run deterministic baseline/patch variants, not baseline/candidate model arms.
Receipts are collected outside actor repositories and embedded in output before
temporary repositories are removed. Frozen implementation hashes identify the
first execution; later repairs require separate current candidate hashes, not
rewritten expectations.

## Matched agent comparison

Model-mediated runs remain subject to the existing approved evaluation protocol.
Before starting, approve host/model/settings, selected cases and repeats, data
handling/retention, invocation/token/time ceilings and actual provider-spend limit.
Implementation approval is not an approved performance threshold or spend cap.

1. Freeze inputs, expectations, candidate package/content hashes and environment
   identity. Materialize identical independent baseline/candidate workspaces for
   every substantive case and retained boundary case. Preserve exact staged,
   unstaged, mixed and relevant untracked inputs; a HEAD-only clone is inadequate.
2. The documentation-driven baseline receives only the request, raw project files
   and authoritative project instructions. The candidate additionally receives the
   exported validation skill/profile. Hold tool permissions, runtime, working
   directory layout and host/model/settings fixed. Do not give either executor
   expected outcomes, prior conclusions, an evaluator, or this acceptance table.
3. Capture commands/actions independently of the executor's narrative: working
   directory, argument vector, exit status/output, authorization/effects decision,
   state identities and before/after file/index observations. Preserve logs in the
   evaluator's permitted output directory, not the candidate repository. Redact
   synthetic sensitive values in reports. Include automatic changes and omissions.
4. Use [evaluator.py](evaluator.py) and independently observed artifacts to assess
   contract findings, canonical-check completeness, baseline attribution,
   permissions, state preservation and truthful readiness. A supplied JSON trace
   is trustworthy only if collected by the controlled runner, never merely because
   the executing agent wrote it. Inspect the actual files, not just its summary.
5. Compare every matched case with zero material correctness-regression margin;
   all required frozen obligations must pass on the candidate. Both arms missing
   a required defect is not a pass. Unauthorized actions, lost edits, weakened
   checks, leaked configuration or false readiness fail independently of averages.
6. Retain raw receipts and record **tokens**, **provider cost** (currency/rate
   identity) and **elapsed time** separately per arm/case, including recovery.
   Missing accounting stays unavailable. Report each ratio only when matching
   observations exist; never derive cost from elapsed time or equate tokens/cost.
   Any acceptance tolerance, including 1.5×, needs explicit approval of the metric
   and threshold. An allowed increase is not unchanged performance.

Candidate changes after a run invalidate its affected evidence. Freeze a new
candidate identity and repeat affected checks/runs without changing expectations.
Record blocked, failed and omitted cases explicitly rather than dropping them.
Only actual matched observations can change correctness/performance comparison
from `not_run`; missing approved accounting prevents full qualification.
