# This repository

Authority: README, CONTRIBUTING, current skill methods and `inventory.json`.
Protected contracts: Iterate phases/manual checkpoints, CLI-owned local state,
feature arguments/fast paths, canonical helper, source-grounded 5→3→1 review,
reference-only model selection, three parent entrypoints and complete bundles.

Prerequisite: Python 3.11+; existing suitable `.venv` with development requirements
for metadata checks. Do not install dependencies without applicable authorization.
Canonical local checks, from repository root:

```sh
.venv/bin/python scripts/build_skills.py --prepare
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/validate_skills.py
```

The distribution tests/check are applicable after those resources exist; a missing
command is a blocker, not a fabricated pass. Exporter prepares generated local
resources and emits a self-contained zip; installer tests use temporary projects.
Do not commit state, scratch, caches or archives. Docs/static checks do not certify
model adherence, real host invocation, scientific validity or live workloads.

Permission scope: requested local edits/checks only. No Git mutations, global
installation, publication/deployment or model-mediated evaluations are implicit.

[Shared usage](../usage.md) owns grammar/defaults. Help/status/list are read-only;
work/deferral require explicit or human-established targets, not recency. Iterative
manual acceptance remains, with an agreed task-appropriate surface and essential
protections from the start. Real helper/package effects and documentation governance
are not assistant-routing/user-comprehension acceptance.
