# Focused six-method verification

Scope: `develop bdd`, `develop prd`, `develop prompt`, `develop backlog`, `review
code` and `review smells` only. [Traceability](traceability.json) records supplied
requirement → maintained instruction/reference → worked output → verification.
Retained/generalized/excluded dispositions are about method portability, not
permission to execute the source documents' historical requests.

## Evidence separation

- Runtime demonstrations live in the six package-local `*-worked.md`
  resources. They provide complete, synthetic inputs and outputs and are explicitly
  illustrative, not observed agent results or held-out answer files.
- `cases.json`/`expected.json` contain the held-out revised-review and structural
  cases. `bdd-prd/` and `prompt-backlog/` contain independent held-out development
  cases. Inputs and evaluator criteria are separate; executing agents receive only
  one request/context and its raw artifacts, never `expected.json`, prior conclusions
  beyond those supplied as case inputs, or this evaluation directory wholesale.
- This work does not change safety fixtures in `../fixtures.json`, `../expected.json`,
  `../review/` or the combinations freeze. They complement the realistic
  execution cases; successful new examples cannot erase a safety regression.
- `baseline.json` captured current workspace instructions before this PRD's edits,
  including pre-existing uncommitted review improvements. It is **not** a pristine
  Git revision or the original Riskonnect implementation. Source content and hashes
  are retained; unchanged dependencies are pinned for package reconstruction.
- `freeze.json` pins baseline, raw-case and evaluator-criteria hashes. `results.json`
  records actual checks and separately unperformed checks. Neither is an answer
  supplied to an executing agent; evaluation material is excluded from exports.

## Local deterministic checks

From the repository root, using its existing development environment:

```sh
.venv/bin/python -m unittest tests.test_bdd_prd_methods tests.test_prompt_backlog_methods tests.test_workflow_methods -v
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

These checks execute inert local example/fixture code, verify intended behavioral
red then green for BDD, strict prompt contracts and accepted replay, source-grounded
review/audit consequences, registers and snapshot/criteria integrity. They do not
make external writes or call models. Static document/link/register checks remain
governance evidence, not behavioral acceptance or proof of generation quality.
Packaging checks only support usable reference closure, not a new distribution
workstream or authorization to install, release or publish.

## Paired model-mediated protocol — not run

The existing [approval protocol](../protocol.md) governs access, host/model settings,
permitted synthetic data, retention and approved spend/token/time ceilings. This PRD
does not approve extra model evaluation; implementation subagents are not held-out
evaluators. Do not infer budget or certify agent fidelity from their agreement.

After explicit access/budget approval:

1. Select the six realistic method cases and applicable unchanged safety fixtures.
   Freeze selected inputs/criteria before execution. Materialize only bounded raw
   artifact paths in isolated workspaces; no live tracker/model/clinical access.
2. Reconstruct current-instruction baseline from `baseline.json` and its captured
   inventory, verifying every unchanged dependency hash. Retrieve a hash-matching
   saved or version-controlled dependency if concurrent work changed the local copy;
   never substitute the newer unmatched file. Candidate receives revised
   package-local instructions. Baseline must not receive candidate-only worked
   resources; neither side receives evaluator expectations. Any missing dependency
   blocks comparison rather than being filled from an unverified newer version.
3. Run matched inputs, tools, permissions, host/model/settings and completion
   limits. Change only instructions; include their content hashes in each record.
   Preserve actual output artifacts and actions, refusals, errors and omitted checks.
4. Independently assess outcomes and method fidelity: genuine behavioral red before
   production changes; complete preferred-design handoff; coordinated prompt
   surfaces with unchanged identity/time ownership; primary/enabling/validation
   coverage; complete revised dispositions; demonstrated structural consequence
   and complexity-reducing remedies. Check forbidden actions and scope as strictly
   as missing acceptance outcomes. Do not score heading/keyword similarity.
5. Compare frozen-current versus revised artifacts, consequential omissions, scope
   and methodological fidelity on equivalent evidence. No material unexplained
   regression is acceptable; inspect contradictory/borderline results under the
   existing bounded recovery protocol. Report missing telemetry/baselines honestly.

Required record: case and instruction/input hashes, host/model/settings, permissions,
outputs and action trace, artifact/omission/scope/fidelity assessment, regression
disposition, checks actually performed, available time/tokens/cost and limits.
Do not modify global host/release/quality gates without their existing approval and
source-bound evidence. No runs or performance/quality parity are claimed here.

## Source context boundaries

Riskonnect's supplied review instructions, BDD authoring preferences, compact PRD
memory, development guide, ticket template, worked reconciliation and project guide
are contextual source evidence. Portable methods are retained/generalized; exact
clinical timestamps live in the reference profile. Riskonnect-only facades, journal
widths, provider wiring, no-Databricks-access rule, issue keys, source priorities and
historical decisions are not universal commands, default identities or current
tracker facts. No Riskonnect files or external systems are edited in this work.

Completion limits: local examples and deterministic validation can pass while
model/host comparisons remain `not_run`. That limitation blocks full method-quality
acceptance, not the requested source implementation. The separate Python smell
guide is unavailable; no completeness claim is made for its unknown contents.

## Canonical document relocation

Current method and worked documents live beside each skill's `SKILL.md`;
local `references/` folders are ignored and are not runtime dependencies.
Frozen baseline content, traceability identifiers and recorded results retain
their historical paths and hashes. Resolve a frozen `skill/references/file.md`
identifier to `skill/file.md` only when checking the current implementation;
reconstruct historical comparisons from their captured content and pinned
dependencies, never substitute the relocated current guidance as a baseline.
