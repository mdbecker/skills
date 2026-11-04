# Agent-template reference profile

This historical reference applies to the Databricks agent template, not every
target repository. Read the target's current `AGENTS.md`, README,
`docs/ARCHITECTURE.md`, `.pre-commit-config.yaml`, `noxfile.py`, and relevant
implementation/job configuration before using it. Prefer a suitable existing
repository-local environment. Source documents establish contracts, not permission
to install, fix, access Databricks or deploy.

## Canonical workflow and effects

Reference canonical check:

```sh
python3.12 -m pre_commit run --all-files --show-diff-on-failure
```

The local hook selects `./.venv/bin/python -m nox -s precommit` when available,
otherwise `python -m nox -s precommit`; that does not remove Python 3.12 or tool
prerequisites. Inspect this selection and all notified sessions before running.

| Workflow | Checks and effects |
|---|---|
| Hygiene hooks | Merge conflict, YAML/TOML checks, end-of-file and trailing-whitespace fixes; initial hook environments may need installation/network access. |
| `lint` via `precommit` | Ruff format and `ruff check --fix`; installs tool requirements and the editable project even with reused environments. |
| `tests` | Unit and contract tests; coverage reports and a 90% gate; installs dependencies/editable project. Focused `unit`/`contract` use no coverage and are not substitutes. |
| `build_wheel` | Installs build requirements, removes `build/` and `dist/`, then rebuilds/validates the wheel. Inspect the invoked build script and its outputs. |
| `markdown_lint` | Installs its Markdown lint tool and scans README, AGENTS and docs. |

The manual `nox-ci` hook runs `nox -s ci` with check-only Ruff behavior, but can
still install dependencies, write coverage and remove/rebuild artifacts. It is
not an automatically authorized read-only replacement. Hook installation
(`python3.12 -m pre_commit install`) is separate workstation setup.

Resolve formatting, installation and destructive cleanup against allowed scope
**before** execution. If they conflict, request authorization or propose an approved
isolated run of the actual intended state, with remaining effects disclosed.
Focused diagnostics never replace the required full canonical command. Never
lower the 90% coverage gate or bypass hooks to manufacture green validation.

## Contract obligations and relevant checks

For affected areas record **obligation → authoritative project source → relevant
check → observed result**. The checks below describe required observations, not
invented test names; locate current tests and entrypoints in the target project.
If sources or coverage are unavailable, mark the finding/gap, not a pass.

| Area | Required behavior | Authoritative project source | Relevant check |
|---|---|---|---|
| Tools | The full discovered inventory reaches the model; runtime selection stays model-driven, with no default manual allowlist or deterministic Python routing. The `customer_account_brief` starter calls at least one tool and answers from its output. | `AGENTS.md` Core Template Invariants; architecture Tool Source Discovery/Agent Runner Loop; canonical `examples/demo_run_task.json`; current registry/runner. | Local unit/contract tests with a synthetic model and tool outputs: capture all model-visible specs, let the synthetic response choose a tool, observe execution and output grounding. The read-only demo chooses `lookup_customer`, not the available write-like `create_support_ticket`. No live LLM call is needed for these checks. |
| Configuration | Unknown top-level and nested keys fail; all Databricks SDK clients use the shared factory. | Architecture Config Loading; maintainer rules; current `config.py` and `clients/databricks.py`. | Invalid-key configuration tests; inspect affected client construction and locally mock factory/auth propagation through LLM, MCP and preflight consumers. The factory location is an explicit contract, not a universal package-layout rule. |
| Storage | A configured events table requires active Spark; initialization/write failures never silently fall back to local files. Without a table, configured local JSONL persistence remains valid. | Architecture Storage/Event Persistence; current storage routing. | Table/no-Spark and table-write failure tests assert failure and no local output; local-route tests assert expected persistence using temporary files. |
| Packaging/jobs | Console entrypoints raise `SystemExit(code)`; package-root wheel entrypoints return without exit on success and raise `SystemExit(nonzero)` on failure. Jobs use aligned entrypoints and canonical task/configuration references. | Architecture CLI/Wheel Entrypoint Flow; maintainer rules; current `pyproject.toml`, package entrypoints, `databricks.yml`, `resources/jobs.yml`; canonical task and `workspace-config.yml`. | Exercise console/wheel success and failure using local mocks; inspect built-wheel entrypoints and job wiring/arguments against those references. Successful wheel construction alone does not prove job wiring or deployed behavior. |
| Tests | Protect observable behavior and stable contracts, not incidental internal structure or noncontractual exact event ordering. | `AGENTS.md` Testing philosophy; current public contracts and affected tests. | Inspect assertions against a cited contract; verify required events and meaningful before/after relationships unless exact order is documented. Keep full unit/contract/coverage validation. |

These are reference-specific obligations. Transfer only the mapping procedure to
another project; do not impose Spark, Databricks SDK factories, Python, this coverage
threshold or model-driven routing on a project that does not require them.

## Preservation and reporting

Record starting revision, intended changes, unrelated staged/unstaged edits and
relevant untracked inputs before checks; compare file content and staging after.
Report automatic fixes and preserve mixed edits without resetting, deleting or
unstaging user work. Excluded staged paths include `.pytest_cache/`, `__pycache__/`,
`.local_state/`, `dist/`, `build/`, `*.egg-info/` and `.coverage`; inspect sensitive
configuration without printing its values. A finding is not cleanup permission.

Classify failures as patch-related, baseline-confirmed pre-existing, environmental
or unresolved with command/source evidence. Associate results with the actual
tested state and rerun affected checks after subsequent changes.

The deployment guide's smoke check is a deployed job, not only bundle validation.
This defines the boundary of reporting: it does not authorize deployment, job runs
or Databricks access. Local tests, coverage and wheel checks never establish live
LLM, live-agent or deployed-workload verification.
