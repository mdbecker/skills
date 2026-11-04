# Skills

Two Codex skills for building and challenging software:

- **`/iterate` — Build something.** Establish the architecture, build a minimal happy path, get hands-on feedback, refine it, then test and finalize.
- **`/debate` — Challenge it.** Run five independent Luna reviews, three Terra reconciliation passes, and one Astra synthesis, checking findings against actual source evidence.

The skills work independently. Debate is an optional review tool, not a required gate in Iterate.

## Install

Clone the repository:

```sh
git clone https://github.com/mdbecker/skills.git
cd skills
```

This checkout includes project-local discovery links in `.agents/skills/`, so both skills are available when working here. To use them in another project, link the skill directories into that project's `.agents/skills/` directory:

```sh
mkdir -p /absolute/path/to/your-project/.agents/skills
ln -s /absolute/path/to/skills/iterate /absolute/path/to/your-project/.agents/skills/iterate
ln -s /absolute/path/to/skills/debate /absolute/path/to/your-project/.agents/skills/debate
```

Replace the example paths with your actual checkout and project paths. If a destination already exists, inspect it before replacing it. The links keep installed skills current when you update this checkout.

Use your Codex skill picker to invoke either skill. The examples below use `/iterate` and `/debate`; hosts that use `$iterate` or `$debate` can invoke the same skill instructions with that syntax.

## Iterate

```text
/iterate csv-import
/iterate csv-import TWEAKING
/iterate park "Reject duplicate deliveries"
/iterate list
```

Iterate follows six phases:

1. **ARCHITECTURE:** record the impact, exclusions, data flow, and real design tradeoffs; agree on direction with the user.
2. **HAPPY_PATH:** implement the smallest useful flow and park additional concerns.
3. **TEST_BED:** provide a basic web UI and an editable Python driver, run the flow, and hand it to the user.
4. **TWEAKING:** change, run, observe, and repeat until the user says the behavior feels right.
5. **TESTING:** add a few meaningful integration tests for the stabilized flow.
6. **FINALIZATION:** address or explicitly waive deferred work one item at a time.

The bundled manifest helper requires **Python 3.11+** and uses only the standard library. Run it from the project being developed, using the installed helper's absolute path:

```sh
python3 /absolute/path/to/skills/iterate/manifest.py --help
python3 /absolute/path/to/skills/iterate/manifest.py status -v
```

State lives in that project's `.ai-state/` directory. It stays local and supports later-session resumption. The state directory and manifest files must not be symlinks. Feature-specific test-bed files stay in `testbed/scratch/`; reusable tools can be promoted to `testbed/tools/`.

Git projects can use phase commits and small PRs. Local-only projects retain the same six phases and feedback checkpoints without requiring Git, a remote, or PRs. See [the full Iterate instructions](iterate/SKILL.md).

## Debate

```text
/debate review the current implementation and its diff against main
/debate review src/importer.py and its integration tests
/debate discuss "Should this import run synchronously or as a job?"
```

Debate runs entirely through Codex subagents. It needs access to these model selections in the host:

| Stage | Agents | Model | Responsibility |
|---|---:|---|---|
| Independent review | 5 | `gpt-6-luna` | Examine complementary aspects of the same source and baseline |
| Reconciliation | 3 | `gpt-6.1-terra` | Each checks every candidate, disagreement, and supporting claim |
| Final synthesis | 1 | `gpt-6-astra` | Combine supported findings into the final response |

Stages run in order and are batched to respect available concurrency. Missing models or delegation support are reported rather than silently substituted. Codex access and usage limits still apply; the skill requires no separate API token, provider login, Python package, or standalone review CLI.

Findings must include source locations, concrete evidence or a safe reproduction, impact, severity, and the smallest reasonable fix. Agreement between reviewers is not verification. Reports distinguish verified defects, conditional claims, preferences, unresolved disagreements, and coverage limits. Cost information is reported only when available, with estimates labeled as estimates.

Reviews do not authorize code changes or publishing comments. See [the full Debate instructions](debate/SKILL.md).

## Development checks

Python 3.11+ is required. Create a development environment and run:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s iterate/tests -v
.venv/bin/python scripts/validate_skills.py
```

The tests cover manifest behavior. Metadata checks do not prove that models will follow a skill correctly; behavioral changes also need hands-on evaluation.

## Layout

```text
iterate/             Development skill, manifest helper, and regression tests
debate/              Prompt-only hierarchical review skill
.agents/skills/      Project-local discovery links
scripts/             Skill metadata and installation-link checks
.github/workflows/   Automated validation
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for change guidelines, [NOTICE](NOTICE) for provenance, and [LICENSE](LICENSE) for the MIT license.
