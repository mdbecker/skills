# Repository validation acceptance

This corpus exercises develop validate-repo through fictional local projects.
It does not certify other methods, host invocation, model quality or deployed
workloads. qualification.json records the actual scope of available observations.

## Inputs and isolated execution

cases.json contains selected requests, source files, allowed actions and command
mappings. expected.json is evaluator-only; freeze.json binds the current input
identities. The fixture materializer creates disposable repositories with executable
behavioral tests and deliberately mixed source/index states. No installation,
real credentials, network services or live systems are needed. Missing runtimes
block the affected observation rather than being replaced with simulated success.

| Case | Required observation |
|---|---|
| Storage/session contract | A missing Spark session raises instead of silently selecting local storage. The fixture supplies its own contract; no Spark installation is needed. |
| Focused versus canonical checks | Focused success does not conceal a failing required full gate. |
| Baseline attribution | The same failure is observed on equivalent baseline/candidate inputs using the same command and runtime. |
| Formatting and mixed edits | Only explicitly permitted formatting changes; unrelated staged/working edits and the index are preserved. |
| Sensitive configuration and generated assets | Report categories and locations without leaking values or altering staging. |
| JavaScript transfer | Execute the project's actual dependency-free Node/npm tests without substituting another check engine. |

```sh
.venv/bin/python -m unittest discover -s tests -p test_validation.py -v
.venv/bin/python -m evaluations.validation.evaluator --output /tmp/validation-evidence.json
```

Fixtures expose materialize, snapshot, record and trusted_records. Actor context
contains only the request, raw inputs, runtime and command mapping. The evaluator
uses independently captured receipts and actual file/index observations; actor
narrative alone is not trusted evidence. Command/data text is never execution
permission. Fixture execution is not a model-mediated comparison.

## Observed actor comparisons

The existing evaluation protocol governs approved tools, model/host settings,
data/retention, repeats and token/time/spend limits. Materialize matching input
identities, preserve allowed mixed edits, and capture actual commands and effects.
Do not give the actor expected criteria or evaluator answers. Required omissions,
unauthorized effects, changed indexes, leaked values and false readiness fail
independently of summary averages. Missing accounting is unavailable.

Correctness and performance remain not-run until actual approved matched trials.
Any tolerance needs an explicit agreed metric/threshold. Repeat affected checks
when candidate inputs change without changing expected outcomes to match failure.
Local checks, host invocation, model behavior and release approval are separate.
