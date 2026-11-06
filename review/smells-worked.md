# Complete consequence-grounded structural audit

## Contents

- [Scope, contracts and raw evidence](#scope-contracts-and-raw-evidence)
- [Complete audit output](#complete-audit-output)
- [S01 — Divergent retry policies omit a terminal event](#s01--divergent-retry-policies-omit-a-terminal-event)
- [S02 — Repeated event fields have inconsistent owners](#s02--repeated-event-fields-have-inconsistent-owners)
- [S03 — One configuration option requires scattered coordinated edits](#s03--one-configuration-option-requires-scattered-coordinated-edits)
- [Reviewed counterexamples — no findings](#reviewed-counterexamples--no-findings)
- [File-level coverage](#file-level-coverage)
- [Dependency-aware remedy plan](#dependency-aware-remedy-plan)

Synthetic reference-style workflow runner and fictional deployment configuration.
This is a complete illustrative report over the raw sources below, not a claim that
findings exist in a target project. Locations count from the first
line in each block. None of the proposed remediation is applied by an audit.

## Scope, contracts and raw evidence

Request: “Audit this runner/configuration slice, read-only. Rank structural findings,
include file-level coverage and plan dependency-aware remedies.” These eight sources
are the entire accessible slice; a ninth file, `transport.py`, is declared in scope
but unavailable. Tests and generated configuration are supporting evidence, not
additional production finding scope. No comparison base or required external
reference is supplied. No metrics are inferred from historical file counts.

Contracts: attempt 2 is terminal; persist exactly one terminal event before returning
failure. `normal_run` and `validated_run` are existing public facades. Event indexes
increase only after successful persistence. Application-supplied `processed_at`
owns record time, distinct from a document's `issued_on`. Keep schemas, safe errors,
redaction and runtime YAML-over-environment precedence. Local and deployment timeout
defaults must agree. No producer, configuration or transport API changes authorized.

`retries.py`:

```python
def normal_run(attempt, persist):
    if attempt == 2:
        persist("terminal")
        return "failed"
    return "retry"


def validated_run(attempt, persist):
    if attempt == 2:
        return "failed"
    return "retry"
```

`events.py`:

```python
def emit_ok(run, source, persist):
    event = {"run_id": run["id"], "index": run["next_index"], "recorded_at": source["processed_at"], "status": "ok"}
    persist(event)
    run["next_index"] += 1


def emit_failed(run, source, persist):
    event = {"run_id": run["id"], "index": run["next_index"], "recorded_at": source["issued_on"], "status": "failed"}
    run["next_index"] += 1
    persist(event)
```

`fields.py`:

```python
ALLOWED_KEYS = {"timeout_seconds"}
ENVIRONMENT_KEYS = {"timeout_seconds": "APP_TIMEOUT"}
```

`config.py`:

```python
from fields import ALLOWED_KEYS, ENVIRONMENT_KEYS


def load_config(values, environment):
    if set(values) - ALLOWED_KEYS:
        raise ValueError("unknown configuration")
    raw = values.get("timeout_seconds", environment.get(ENVIRONMENT_KEYS["timeout_seconds"], 15))
    timeout = int(raw)
    if timeout <= 0:
        raise ValueError("timeout must be positive")
    return {"timeout_seconds": timeout}
```

`render.py`:

```python
def render_environment(values):
    return {"APP_TIMEOUT": str(values.get("timeout_seconds", 30))}
```

`deployment.txt`:

```text
Pass APP_TIMEOUT from render_environment to the runtime environment.
Other rendered settings are not forwarded unless added to this allowlist.
```

`models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class RunResult:
    status: str
    attempts: int
```

`api.py`:

```python
from models import RunResult
from retries import normal_run, validated_run


def run(attempt, persist, validated=False):
    policy = validated_run if validated else normal_run
    return RunResult(policy(attempt, persist), attempt)
```

## Complete audit output

Snapshot: the eight supplied current sources. Inventory: nine declared files;
eight fully inspected, `transport.py` unreviewed because unavailable. No whole-repo
or performance claim. The DTO and public facade are already useful boundaries.
The pressure points are duplicated transitions, repeated event ownership, and
configuration knowledge split across runtime and deployment.

### S01 — Divergent retry policies omit a terminal event

Structural severity **S3**, family duplicated state-transition policy; recommended
urgency **Must fix before merging**, not an S-level synonym.

- Locations: `retries.py:1` and `retries.py:8`; terminal difference at lines 3/10.
- Evidence/consequence: both routes return `failed` at attempt 2, but only normal
  persists `terminal`. A validated run loses its required final journal event.
  Attempts 0 and 1 have matching retry behavior, so separate broad machines are
  not justified by this observed terminal difference.
- Preferred remedy: one shared terminal/continuation transition owns recording
  before return; both public functions delegate to it. Keep any genuinely distinct
  validation decision as a small policy, not more booleans in another mega-loop.
- Why lower complexity: there is one terminal side effect to repair/test instead
  of two duplicated branches. Do not introduce a registry or new command surface.
- Preserve: facades/signatures, attempts 0/1 retry outcomes, one terminal event,
  persistence-before-result ordering, unchanged persistence error propagation.
- Validation: characterize both routes across attempts 0–2, event traces and write
  exceptions. Existing sources locally reproduce `['terminal']` versus `[]` at
  attempt 2. Remedy checks remain proposed; the audit does not edit production.

### S02 — Repeated event fields have inconsistent owners

Structural severity **S3**, families data clump / duplicated ownership; recommended
urgency **Should fix now**. Independent dimensions, not mechanical S3→urgency.

- Locations: `events.py:2–4` and `events.py:8–10` in this supplied snapshot.
- Evidence: the same four fields are built twice. Success uses `processed_at`
  and advances after persistence; failure uses `issued_on` and advances first.
- Consequence: a failed write consumes an index on one path but not the other;
  later journal rows have gaps. Failed-event record time instead describes document
  issuance. Adding a field/default requires coordinating both constructors and
  risks further drift. Repeated syntax alone would not establish this finding.
- Preferred remedy: one recorder constructs the fixed envelope from application
  context, validates/redacts under the existing contract, persists, then advances
  the index. Producers supply a small status draft, not index/time copies. Keep
  existing `emit_ok`/`emit_failed` public signatures as facades if consumed.
- Why lower complexity: remove duplicated envelope/index/time decisions rather
  than relocate both dictionaries into two new modules. No schema widening,
  new event types or assumption that issued and processing times are interchangeable.
- Preserve: fixed row keys/types, ordering, failure behavior, reviewed redaction
  and safe diagnostics. This fixture contains no sensitive payload and establishes
  no broader security correctness; real producer redaction requires separate tests.
- Validation: a raising persistence boundary leaves indexes unchanged; successful
  records advance exactly once and use the app-owned processing instant on both
  paths. Check sensitive sentinels where that actual project supports payloads.

### S03 — One configuration option requires scattered coordinated edits

Structural severity **S2**, family shotgun surgery; recommended urgency **Should
fix now**. Not a complaint about file length or number of modules.

- Locations: `fields.py:1–2`, `config.py:7–11`, `render.py:2`, `deployment.txt:1–2`.
- Evidence: name/allowlist/environment binding live in one file, parsing/default
  in a second, deployment binding/default in a third, forwarded names in a fourth.
  Empty input gives runtime timeout 15 but rendered timeout 30, a concrete drift.
- Consequence: adding one option requires updating four independent owners; omitted
  render forwarding can silently leave production at another setting/default.
- Preferred remedy: one small declarative field table owns supported name, env
  name, default and scalar coercion. Runtime parser and deployment renderer consume
  it; deployment forwards the resulting supported environment mapping. Keep any
  cross-field invariants explicit outside the table. No plugin/schema framework.
- Why lower complexity: one source for already-duplicated variation and one shared
  default, not four catalogs plus generated duplicates requiring manual maintenance.
- Preserve: supported keys/environment names, YAML precedence, positive integer
  validation and reviewed error text. Canonical default 15 follows current runtime;
  if an owner-intended change to 30 exists, surface that business decision explicitly.
- Validation: local default equals rendered default; explicit YAML overrides env;
  invalid/nonpositive values still fail; supported fields reach deployment unchanged.

### Reviewed counterexamples — no findings

`models.py` is a cohesive immutable data-only transfer contract, used by `api.py`.
Methods or splitting one field per object would add ceremony without improving
ownership. `api.py` is a public facade selecting existing policies and presenting
their result; retain it. Do not attach a size/DTO/protocol finding quota. A long
single-purpose parser could likewise remain cohesive when its real behavior and
change axes support it; this audit did not inspect such a parser and claims no
finding or clearance for an imagined file.

### File-level coverage

| File | Inspection | Result |
|---|---|---|
| `retries.py` | Complete | S01 |
| `events.py` | Complete | S02 |
| `fields.py` | Complete | S03 |
| `config.py` | Complete | S03 |
| `render.py` | Complete | S03 |
| `deployment.txt` | Complete | S03, support configuration in declared scope |
| `models.py` | Complete | No material finding: cohesive immutable result |
| `api.py` | Complete | No material finding: consumed facade/presentation boundary |
| `transport.py` | Unreviewed | Source unavailable; no absence or clearance claim |

### Dependency-aware remedy plan

1. Establish the event recorder seam (S02) and characterize ordering/errors before
   routing both terminal branches through shared transition ownership (S01).
   Changing the loop first while its event ownership still diverges risks carrying
   the defect into a new abstraction. Retain the facade and output schema.
2. Configuration ownership (S03) is independent and may proceed without runner
   decomposition. Resolve any real default change before broadening the increment.
3. Recheck each affected producer/config consumer and original event traces. No
   DTO rewrite, public API removal, transport redesign or speculative registry.

Checks/limits: repository tests reproduce terminal omission, failed-persistence
index drift, timestamp disagreement and 15/30 default divergence from these exact
inert sources. They verify locations against supplied blocks and coverage against
the declared inventory. These are actual local fixture checks when recorded in the
evaluation results, not applied remedies, model adherence, hidden-source inspection,
live workload checks or an unavailable external reference. The eight-file sample cannot
clear `transport.py` or any other repository. Audit remains read-only.
