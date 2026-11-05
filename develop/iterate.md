
# Iterate

For a justified specialization/handoff, read only the relevant [optional recipe](resources/combinations.md).
It does not restart this lifecycle, require sibling installs or replace user checkpoints.

This is the canonical feature lifecycle selected by `/develop iterate`.
Its helper is `scripts/manifest.py` in this skill directory. Parse the parent
mode before resolving work/status/defer/list, contextual targets, or legacy forms
with [shared usage](resources/usage.md#iterate). Read shared policy without silently
changing the lifecycle or state ownership.

Feedback-driven implementation uses persistent project state. Agree direction,
implement a minimal primary flow, exercise it manually, and refine it with the user
before stabilizing the regression suite. Required project checks and essential
access, integrity, and resource protections apply from the start. Only discretionary
completeness is deferred; it is not forgotten or mistaken for safe delivery.

## State Manifest & CLI

State lives in the project repo at `.ai-state/<feature-name>.json`. This file is the source of truth across sessions — always trust it over memory of prior conversations.

The state directory and manifest files must be real local paths, not symlinks. If existing state uses symlinks, stop and explain the policy; do not replace links or move their targets automatically. The user can copy the state into a local `.ai-state/` directory before resuming.

**All manifest reads and writes go through the CLI** bundled as `scripts/manifest.py` in this skill directory. Resolve its absolute path from the installed skill directory, then run `python3 "<skill-directory>/scripts/manifest.py"` from the project root. In the examples below, `manifest.py` means that command; do not assume it is on PATH. Never hand-edit the JSON — the CLI checks required top-level keys, phases, and backlog item fields, stamps `last_updated`, and fails loudly on corruption. Run `manifest.py --help` and `manifest.py <cmd> --help` for full usage.

On damaged state, stop and preserve the file. Ask the user to restore a known-good
local copy or authorize separate maintenance; do not reset, synthesize missing
keys, or interpret validation failure as a missing feature.

The helper validates required nested fields, list entries, actual booleans, and
JSON-compatible values before any handler writes state or updates timestamps.
Duplicate keys, malformed sections, and invalid entry types fail without rewriting
the file. Compatible extra fields and optional `next_step`, `phase_history`, and
`test_bed_commands` omissions remain supported; read-only commands do not backfill
them on disk. Validation does not add phase-order or minimum-option gates.

Tool-registry storage must remain ordinary local directories and a file at
`testbed/tools/registry.json`; links or escaping storage are rejected before access.
Explicitly selected existing external tool references remain supported, but
registration grants no permission to execute them or write an external registry.

| Action | Command |
|---|---|
| New feature | `manifest.py init <feature> --impact "one sentence"` |
| Status dashboard | `manifest.py status [feature] [-v]` (no feature = most recent) |
| List all features | `manifest.py list` |
| Change phase | `manifest.py phase <feature> TWEAKING` (records git commit in `phase_history`) |
| Session handoff note | `manifest.py set <feature> next_step "where things stand"` |
| Render architecture doc | `manifest.py render <feature> [--out PATH]` |
| Park edge case / hardening | `manifest.py park <feature> edge\|hardening "description"` |
| Resolve / waive backlog item | `manifest.py resolve <feature> edge\|hardening <n> [--waive "reason"]` |
| Record test bed command | `manifest.py testbed <feature> add --label "seed db" --cmd "..."` |
| Register / list reusable test bed tools | `manifest.py tool add --name ... --path ... --desc ... [--usage ...] [--feature ...]` / `tool list` |
| Record architecture decision | `manifest.py decision <feature> --title ... --context ... --option A --option B --decision A --rationale ...` |
| Set fields (impact, data_flow, entry_point, exclusion, assertion, ...) | `manifest.py set <feature> <field> "value"` |

## Resolve the requested action

[Shared usage](resources/usage.md#iterate) is the grammar/default authority. These
are assistant instructions, not new helper subcommands.

- Help, bare Iterate, status, and list are read-only. Explain/view the selected
  feature and recency basis when used; no state note, initialization, ignore edit,
  demonstration, or implementation follows. No state means no tracked work.
- Defer and legacy park require an explicit or one human-established feature,
  never modification-time selection. Call the helper with its explicit positional
  ID/kind/description, show the recorded follow-up, and stop. No test/ticket/fix.
- Work and unambiguous legacy feature forms need a resolved target and outcome.
  Show the ID/effect. Resume existing state; a missing resume target is not a new
  feature. Initialize only established start-new intent, ID, and impact; then add
  the local state ignore rule and start ARCHITECTURE. Do not interpret corruption
  or a misspelling as absence. Clarify action-like IDs rather than renaming them.
- An explicit work phase override applies only to the selected existing feature.
  Record the old/new stage, then display status. A new feature begins in architecture;
  a phase record is not proof that earlier exit criteria passed.

Only authorized work adopts the phase constraints. Show its status dashboard and
[readable stage label](resources/usage.md#phases), with real limits and prior
acceptance. Record meaningful work decisions and transitions immediately via the
CLI. Do not write state merely to answer help/status or an argument question.

Manifest schema (managed by the CLI; shown for reference):

```json
{
  "project_metadata": {
    "feature_name": "",
    "last_updated": "",
    "current_phase": "ARCHITECTURE | HAPPY_PATH | TEST_BED | TWEAKING | TESTING | FINALIZATION",
    "next_step": "free-text handoff: exactly where work stands and what happens next",
    "phase_history": [ { "from": "", "to": "", "at": "", "commit": "git sha, if in a repo" } ]
  },
  "core_objective": {
    "impact_target": "one sentence: the exact business outcome this feature delivers",
    "strict_scope_exclusions": []
  },
  "architecture_decisions": [
    { "id": 1, "title": "", "context": "", "options_considered": [], "decision_made": "", "rationale": "" }
  ],
  "implementation_state": {
    "data_flow_description": "inputs -> transformations -> outputs, plus access patterns",
    "test_bed_environment": "prose notes on the environment, if commands alone aren't enough",
    "test_bed_commands": [ { "label": "start services", "command": "docker compose up -d" } ],
    "happy_path_entry_points": []
  },
  "deferred_backlog": {
    "edge_cases": [ { "description": "", "is_resolved": false } ],
    "hardening_tasks": [ { "description": "", "is_resolved": false } ]
  },
  "testing_strategy": {
    "target_execution_path": "",
    "required_integration_assertions": []
  }
}
```

## Universal Rules (all phases)

- **Git permissions are separate.** Phase rituals do not authorize commits,
  branches, squashing, pushes or PR creation. When those actions are not authorized,
  retain the local phase/check summary and user checkpoints without mutating Git.

- **Defer optional completeness.** Record out-of-scope refinements against the
  explicit feature and show the helper's recorded line. Essential safety and in-scope
  correctness are not optional polish: preserve them or contain/block unsafe exercise.
  Do not defer required validation or failure handling merely because of the phase.
- **Phase transitions are explicit.** Obtain required exit agreement before
  advancing, state the next direction, then update via the CLI. Do not imply that
  the helper verifies manual acceptance or ordinary exit criteria.
- **The user can jump phases.** An explicit work `--phase` or unambiguous legacy
  feature/phase request records the selected existing stage. Keep skipped prerequisites
  and unperformed checks visible; do not silently switch implementation approaches.
- **Leave a handoff note.** At the end of every work stint — and before any risky long-running step — run `manifest.py set <feature> next_step "..."` describing exactly where things stand and what happens next (e.g. "handler written, not yet run against docker; seed script at scripts/seed.sh"). The next session's dashboard leads with it; a stale or missing note costs the first ten minutes of that session.

## Comments, Docs & Commits

**Comments:** Write comments only when they add information the code cannot readily convey, such as intent, constraints, or a non-obvious tradeoff. Default to one line; use more when needed for clarity. Keep the voice plain, concrete, and directed at another developer. An available code-commenting skill may help, but none is required.

**Exception — test bed code** (`testbed/` — driver scripts, UI pages, tools) is heavily commented, because the user reads and hand-edits it. The one-line default does not apply there; the same plain voice does. Comments are working notes from one developer to another: what each block does, which lines to change to try different things, gotchas ("server must be up first", "IDs must exist in the seed data"). Keep it casual and concrete — `# bump this to see pagination kick in`, not `# This variable controls the number of rows fetched per request`. No section-banner ASCII art, no docstring boilerplate, nothing that reads like generated documentation.

**Commits** — the git history must read as if a developer wrote it, with no trace of the AI workflow:

**Local-only projects:** If the project has no Git repository, or the user explicitly chooses a local-only trial, record that choice as an architecture decision using the CLI and mention it in `next_step`. Proceed through the same six phases with the same user checkpoints. Do not initialize Git or create a remote merely to satisfy this skill. Omit commits, squashing, pushes, and PRs in local-only mode; record phase transitions without a commit SHA and summarize the local changes and checks instead. A Git project without a usable remote can use this mode after the user chooses it. FINALIZATION then starts after the local TESTING exit and resolves each item after its focused check, without waiting for a nonexistent PR merge.

- **Commit only at the end of a phase** that produced code (typically HAPPY_PATH, TWEAKING, TESTING, FINALIZATION; skip phases that changed nothing tracked). Commit first, then run `manifest.py phase` — the recorded SHA then anchors exactly what that phase produced. No mid-phase WIP commits unless the user asks.
- **Never commit specs or planning artifacts:** `.ai-state/`, plan/design docs, and feature-specific test bed scratch (`testbed/scratch/`); gitignore both at init. **Exception — reusable test bed tools:** pieces likely useful to future features (seed scripts, UI shells, server wrappers) are promoted to `testbed/tools/`, registered via `manifest.py tool add`, and committed along with `registry.json` — they are temporary tooling, kept generic (no feature-specific hardcoding). Do the promotion at TWEAKING or FINALIZATION exit, when it's clear which pieces earned reuse; when in doubt whether something is reusable, ask the user. If a test bed artifact is worth keeping (a seed script others would use), that's a deliberate decision to surface to the user, not a default.
- **Commit messages:** imperative subject line under ~65 chars stating what changed; body only when it earns it — the why, a constraint, or a tradeoff the diff can't show, in one or two short paragraphs of plain prose. No bullet-list inventories of the diff, no phase names or workflow vocabulary ("happy path", "parked", "FINALIZATION"), no co-author/generated-by trailers.

**Product-facing documentation** should describe the product, not irrelevant
delivery-process detail. Skill/workflow manuals must define their inputs, effects,
checkpoints, and limits; architecture/progress reports may show state and phases.
All prose should read like a developer writing for a colleague:

- **Plain words over jargon.** Write for someone who knows the language but not this system. If a term is load-bearing, define it once in a sentence and then use it; if it's decoration, cut it.
- **No flourish.** No "seamlessly", "robust", "powerful", "leverage", "elegant", "under the hood", "it's worth noting that", "in today's fast-paced". No selling the feature — the reader already decided to use it. No exclamation marks.
- **Say the thing, then stop.** One idea per paragraph, two to four sentences. No paragraph that restates the previous paragraph in different words, no closing summary that repeats the page.
- **Concrete over abstract.** A short runnable example beats three paragraphs describing what the example would show. Real identifiers and realistic data, not `foo`/`bar`.
- **Lead with the sharp edges.** The things that actually cost someone an afternoon — the failure that looks like a bug but is a config error, the call that must happen first, the default that surprises — get their own headings or callouts. That's what makes a doc worth reading over the source.
- **No AI tells.** No emoji, no bold-lead bullet lists where every bullet is `**Word** — sentence`, no rhetorical questions as headings, no "Let's dive in", no tables of one-word cells padded to look thorough.
- **Keep the topic clear.** Omit internal process jargon from unrelated product
  docs. When the workflow itself is the topic, explain load-bearing terms rather
  than suppressing phases, state, or follow-up information.

```text
# Wrong (reads like an AI wrote it):
Bentobox's powerful access control system seamlessly empowers you to
secure your artifacts! Under the hood, it leverages a flexible
attribute-based paradigm. Let's dive into how it works.

# Right:
Artifacts can carry an access policy. Once one does, every Hub method
that touches it asks whether the current caller is allowed.

Bentobox does not authenticate anyone and does not store attributes
about anyone. Your application knows who the caller is, and answers
the question when asked.
```

Document settled product behavior alongside its tests and accepted flow. Usage,
safety, and workflow-contract changes need accurate guidance when they change;
they do not wait for a feature phase. Use existing docs navigation and applicable
render checks under their permissions; do not invent a new docs site.

**Pull requests — the goal is a small, reviewable main PR:**

- **The main PR is the happy path plus its tests, and nothing else.** It ships at TESTING exit, before any backlog work. Squash the phase commits into one, push the branch, and open the PR. Everything the workflow deferred stays deferred — that's what keeps the diff small enough for a human to actually read.
- **Each FINALIZATION item is its own follow-up PR** — one edge case (or one closely-related pair), its fix, and its reproducing test, branched off the merged main PR. A reviewer who has already accepted the happy path can review a fifteen-line hardening diff in a minute.
- The PR description is the commit message with a line on how to exercise the feature. Same discipline: no phase names, no workflow vocabulary, no bullet inventory of the diff.
- **The main PR closes with a "Follow-ups" list** — the open backlog, one line per item, plus waived items marked as such with their reason. This is what tells a reviewer the thin diff is deliberate: they can see the malformed-input case and the duplicate-call case are known and coming, rather than assuming they were missed. Generate it from `manifest.py status <feature> -v`, but write it as plain prose lines a reviewer understands out of context ("Rejects duplicate webhook deliveries", not "edge_cases[2]"). Each follow-up PR references the main PR and drops its item from the remaining list.

```text
# Wrong (reads like an AI wrote it):
Implement HAPPY_PATH for csv-import feature

- Added POST /api/csv-import endpoint
- Parses CSV with header row and inserts rows
- Edge cases parked for FINALIZATION phase

# Right:
Add CSV import endpoint feeding the dashboard table

Rows go straight into the table the dashboard already reads,
so no new query path. Assumes a header row; malformed and
oversized files are rejected upstream by the ALB body limit.
```

## Phases

### 1. ARCHITECTURE
Decide direction before code. For each major decision (data storage, access pattern, new service vs. module, sync vs. async, etc.):
- Compare genuine options for unsettled material choices. Reuse an adequate
  approved specification/discussion and verify current assumptions instead of
  manufacturing another options exercise; actual user direction agreement remains.
- Record the outcome in `architecture_decisions` (context, options, decision, rationale).
- Define `data_flow_description`: inputs, outputs, access patterns.
- Write the one-sentence `impact_target` and list `strict_scope_exclusions` (things explicitly NOT in v1).
- **Plan the test bed:** run `manifest.py tool list` and inventory what exists. Identify which registered tools this feature can reuse as-is, which need modification, and which new tools it will need — record the outcome in `test_bed_env` (e.g. "reuse seed-db and ui-shell; extend seed-db with a row-count knob; new: webhook-catcher"). TEST_BED then executes this plan instead of discovering it.

No implementation code in this phase. **Exit when:** major decisions are recorded and the user agrees on direction.

**On exit, ask the user** if they want the architecture doc generated: `manifest.py render <feature> --out <path>` produces a markdown summary (objective, scope, data flow, decisions, test bed plan) from the manifest. It's a generated artifact — regenerate rather than edit it, and never commit it.

### 2. HAPPY_PATH
Implement the primary outcome with its required contracts and protections.
- Defer speculative extensions, optional resilience, and unrelated polish. Do not
  ban required validation, failure handling, or authorization to preserve phase purity.
- Existing project checks and necessary safety-contract verification may occur early.
  Stabilize the wider regression suite after feedback; code-before-test is not BDD.
- Record entry points in `happy_path_entry_points`.

**Exit when:** the primary flow is code-complete against the recorded data flow,
with essential protections checked or the exercise safely contained. Full manual
acceptance follows demonstration/refinement; do not certify unchecked behavior.

### 3. TEST_BED
Make the primary flow manually exercisable through the smallest architecture-agreed
surface: existing application UI, CLI/sample files, native driver/REPL, or a thin page.
Require both web and Python only if acceptance genuinely needs both. The helper's
Python runtime requirement does not dictate the demo language. The test bed is a
feature playground, not a skill dashboard, production interface, automated test
suite, or model-evaluation pipeline.

Keep representative permitted inputs, visible end-to-end outputs/side effects,
editable variables, and reproduction commands. A new server, notebook, dependency,
restricted data source, or live model call needs its actual project/user permission;
no demonstration rule supplies it. No generic scaffolding for planning or checks.

Execute the existing tool plan rather than discovering it again. Feature-local
scratch stays in `testbed/scratch/<feature>`; reuse approved tools before creating
new ones. Shared-tool changes remain generic and preserve old defaults; otherwise
keep a feature-local copy. Update registry usage when an authorized shared invocation
changes; promotion to reusable tooling is deliberate, not an automatic side effect.

Record each successful startup/seed/exercise command with its label through the
helper. Reusing a label replaces it while preserving ordering; remove obsolete
labels explicitly. Run the actual primary flow once and report the result, including
failure, before handing the agreed mechanism to the user. Preserve their edits.

**Exit when:** the agreed mechanism works as a reproducible way to exercise the flow,
an end-to-end observation is recorded, and the user can try it. A reproducible flow
failure can enter refinement; it is not a passed acceptance check.

### 4. TWEAKING
Tight loop: change → run against test bed → observe → repeat. This loop is shared with the user — they try the agreed task-appropriate surface and edit its representative inputs; expect their edits and feedback to drive changes.
- Keep changes small and observable; verify each by re-running the recorded commands (`manifest.py testbed <feature> list`), not by reading code.
- Keep the agreed demonstration working as the feature changes — it is the verification surface for the whole loop. Before touching a user-editable demo, read its current contents immediately before editing and apply a targeted patch that preserves user changes. Scratch files are ignored by Git, so do not rely on `git diff` to detect their edits; do not regenerate the driver wholesale.
- Park only explicitly optional future improvements; required correctness, validation and safety remain in scope.
- Log any decision reversals in `architecture_decisions` (new entry, don't rewrite history).

**Exit when:** the user says the behavior feels right.

### 5. TESTING
Few tests, each one earning its keep.
- Prefer **one comprehensive integration test per flow** that exercises the same path validated in the test bed, over many mocked unit tests. Set `target_execution_path` to that flow.
- Each test should assert the things that would actually break: outputs, side effects, persisted state — list them in `required_integration_assertions` first, then write the test to cover them.
- Protect accepted behavior and required safety contracts; optional deferred
  cases wait for their agreed item. Earlier essential checks do not become
  test-first evidence, and existing green behavior is not manufactured red.

**Exit when:** the happy-path tests pass and run green from a clean environment. In Git/PR mode, ship the main PR: squash the feature branch's commits into one, push, and open it (see Pull requests above). Confirm with the user before pushing. In local-only mode, record the local delivery summary and checks instead. The backlog does not block this; it follows after.

### 6. FINALIZATION
Consume the backlog and interrogate the result. In Git/PR mode, the main PR may still be open: wait for it to merge before creating finalization branches, then branch each item from the updated target branch containing that merge. In local-only mode, start after the local TESTING exit and use the focused-check delivery rule above instead of branches and PRs.
- Work through the backlog **one item at a time** (`manifest.py status <feature> -v` lists them with indexes). No batching — finish and `resolve` one before starting the next.
- **Before touching code for each item, present a short briefing** and pause for the user's take if they're present:
  1. **Why it exists** — the mechanism: what input, state, or timing produces this case, and how likely it is in practice.
  2. **Impact if unhandled** — what actually goes wrong (corrupt data, crash, silent wrong answer) and who hits it.
  3. **Proposed prevention** — the fix in a couple of sentences, at the level of approach not diff.
  4. **Tradeoffs** — what the fix costs (complexity, performance, UX friction, new dependencies) and any alternative worth naming, including "waive it" when the case is unlikely and the fix is expensive.
- Then implement it **with an explicit test that reproduces the edge case** — the test triggers the exact condition from the briefing (the malformed input, the duplicate call, the mid-operation failure) and asserts the prevented outcome. One focused test per edge case, on its own branch off the main PR, opened as its own PR; only then `resolve`. Waived items (`resolve ... --waive "reason"`) get no code and no test. Never leave an item silently unaddressed.
- **After resolving each item, stop and ask the user before starting the next one.** Summarize what was done in a sentence, name the next item, and wait for their go-ahead — this is a hard checkpoint, not a courtesy; do not continue on an unanswered question or assume consent from earlier enthusiasm. The backlog survives in the manifest, so stopping mid-list loses nothing.
- Run the hardening checklist against the final code and park findings as `hardening` items:
  null/empty/malformed inputs · authn/authz on new surfaces · secrets not logged or committed · timeouts and resource cleanup on external calls · concurrent/duplicate invocation · failure mid-operation (partial writes) · pagination or size limits on unbounded data.
- Finish with a short summary: what shipped, what was deliberately excluded, any backlog items left open.

**Exit when:** backlog is fully resolved-or-waived and checklist findings are addressed.

## Red Flags — you are drifting

| Thought | Correction |
|---|---|
| "I'll add unrelated resilience while I'm here" | Defer optional scope; required safety/failure contracts cannot wait. |
| "Every check must wait until TESTING" | Required project/safety checks can occur early; stabilize the wider suite after manual feedback. |
| "This abstraction will help later" | Later hasn't been validated. Write the concrete version. |
| "I remember where we left off" | The manifest is the truth. Read it. |
| "I'll update the manifest at the end" | Sessions die. Update after each step. |
| "Let me commit this progress" mid-phase | Commits land at phase boundaries only. |
| "I'll fold the edge cases in before opening the PR" | The main PR is the happy path. Edge cases are follow-up PRs. |
| "The intro paragraph should sell the feature" | Docs are jargon-free and unflowery. State what it does, then stop. |
| "The plan doc should go in the repo" | Planning artifacts stay local. The code and its commit message are the record. |
