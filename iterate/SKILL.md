---
name: iterate
description: Use when starting or resuming feature work that should follow the iterative workflow - architecture first, minimal happy path, live test bed, tweak loop, minimal robust tests, then edge-case finalization. Invoke at session start to resume a feature, at any phase transition, or when tempted to add error handling/tests/abstractions before the core is validated. Replaces plan-heavy or test-first workflows.
---

# Iterate

Iterative feature development driven by a persistent state manifest. Validate the architecture and happy path against a real, running test bed BEFORE writing edge cases, error handling, or tests. Complexity is deferred, not forgotten — it's parked in a backlog and consumed in the final phase.

**Core principle: nothing gets hardened until it has been proven to work by hand.**

## State Manifest & CLI

State lives in the project repo at `.ai-state/<feature-name>.json`. This file is the source of truth across sessions — always trust it over memory of prior conversations.

The state directory and manifest files must be real local paths, not symlinks. If existing state uses symlinks, stop and explain the policy; do not replace links or move their targets automatically. The user can copy the state into a local `.ai-state/` directory before resuming.

**All manifest reads and writes go through the CLI** bundled as `manifest.py` alongside this `SKILL.md`. Resolve its absolute path from the installed skill directory, then run `python3 "<skill-directory>/manifest.py"` from the project root. In the examples below, `manifest.py` means that command; do not assume it is on PATH. Never hand-edit the JSON — the CLI checks required top-level keys, phases, and backlog item fields, stamps `last_updated`, and fails loudly on corruption. Run `manifest.py --help` and `manifest.py <cmd> --help` for full usage.

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
| Record architecture decision | `manifest.py decision <feature> --title ... --option A --option B --decision A --rationale ...` |
| Set fields (impact, data_flow, entry_point, exclusion, assertion, ...) | `manifest.py set <feature> <field> "value"` |

**Fast paths — handle these and STOP, no phase workflow, no dashboard:**
- `/iterate park "description"` → run `manifest.py park <most-recent-feature> edge "description"` (use `hardening` if the description is clearly a hardening concern), echo the "parked:" line, done. Parking costs one line.
- `/iterate list` → run `manifest.py list`, show the table, done.

**On every other invocation:**
1. Parse the invocation as either no arguments, a feature name, or a feature name followed by one of the six phase names. Reject other forms with a short usage explanation; do not pass the entire argument string to `status`.
2. Run `manifest.py status <feature> -v`, or `manifest.py status -v` when no feature is supplied. If the named feature has no manifest, initialize it with `manifest.py init <feature> --impact "..."` after establishing its impact, add `.ai-state/` to `.gitignore`, and start in `ARCHITECTURE`. If no feature was supplied and none exists, ask which feature to start. Do not treat other errors as a missing manifest.
3. If a phase was supplied for an existing feature, run `manifest.py phase <feature> <phase>` before displaying the dashboard. A new feature starts in `ARCHITECTURE`; establish it before allowing a later phase jump. Show the output of `manifest.py status <feature> -v` verbatim as the re-orientation: phase, impact target, open backlog counts, test bed commands, and the current phase's exit criterion.
4. Adopt the current phase's constraints below. **Record state after every meaningful step** — a decision made, an edge case parked, a phase transition — via the CLI, immediately. Do not batch updates to the end of the session; sessions get cut off.

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

- **Park, don't handle.** Any edge case, failure mode, or hardening concern noticed outside FINALIZATION is parked immediately via `manifest.py park`, with no code written for it. The CLI echoes "parked: ..." — surface that line so the user sees it was captured.
- **Phase transitions are explicit.** Never silently drift into the next phase's work. When the current phase's exit criteria are met, state that, update `current_phase`, and confirm direction with the user if they're present.
- **The user can jump phases.** `/iterate <feature> TWEAKING` sets the phase directly — the manifest records it and constraints switch accordingly.
- **Leave a handoff note.** At the end of every work stint — and before any risky long-running step — run `manifest.py set <feature> next_step "..."` describing exactly where things stand and what happens next (e.g. "handler written, not yet run against docker; seed script at scripts/seed.sh"). The next session's dashboard leads with it; a stale or missing note costs the first ten minutes of that session.

## Comments, Docs & Commits

**Comments:** Write comments only when they add information the code cannot readily convey, such as intent, constraints, or a non-obvious tradeoff. Default to one line; use more when needed for clarity. Keep the voice plain, concrete, and directed at another developer. An available code-commenting skill may help, but none is required.

**Exception — test bed code** (`testbed/` — driver scripts, UI pages, tools) is heavily commented, because the user reads and hand-edits it. The one-line default does not apply there; the same plain voice does. Comments are working notes from one developer to another: what each block does, which lines to change to try different things, gotchas ("server must be up first", "IDs must exist in the seed data"). Keep it casual and concrete — `# bump this to see pagination kick in`, not `# This variable controls the number of rows fetched per request`. No section-banner ASCII art, no docstring boilerplate, nothing that reads like generated documentation.

**Commits** — the git history must read as if a developer wrote it, with no trace of the AI workflow:

**Local-only projects:** If the project has no Git repository, or the user explicitly chooses a local-only trial, record that choice as an architecture decision using the CLI and mention it in `next_step`. Proceed through the same six phases with the same user checkpoints. Do not initialize Git or create a remote merely to satisfy this skill. Omit commits, squashing, pushes, and PRs in local-only mode; record phase transitions without a commit SHA and summarize the local changes and checks instead. A Git project without a usable remote can use this mode after the user chooses it. FINALIZATION then starts after the local TESTING exit and resolves each item after its focused check, without waiting for a nonexistent PR merge.

- **Commit only at the end of a phase** that produced code (typically HAPPY_PATH, TWEAKING, TESTING, FINALIZATION; skip phases that changed nothing tracked). Commit first, then run `manifest.py phase` — the recorded SHA then anchors exactly what that phase produced. No mid-phase WIP commits unless the user asks.
- **Never commit specs or planning artifacts:** `.ai-state/`, plan/design docs, and feature-specific test bed scratch (`testbed/scratch/`); gitignore both at init. **Exception — reusable test bed tools:** pieces likely useful to future features (seed scripts, UI shells, server wrappers) are promoted to `testbed/tools/`, registered via `manifest.py tool add`, and committed along with `registry.json` — they are temporary tooling, kept generic (no feature-specific hardcoding). Do the promotion at TWEAKING or FINALIZATION exit, when it's clear which pieces earned reuse; when in doubt whether something is reusable, ask the user. If a test bed artifact is worth keeping (a seed script others would use), that's a deliberate decision to surface to the user, not a default.
- **Commit messages:** imperative subject line under ~65 chars stating what changed; body only when it earns it — the why, a constraint, or a tradeoff the diff can't show, in one or two short paragraphs of plain prose. No bullet-list inventories of the diff, no phase names or workflow vocabulary ("happy path", "parked", "FINALIZATION"), no co-author/generated-by trailers.

**Documentation** — any prose this workflow produces (docs-site pages, READMEs, PR descriptions, the rendered architecture doc) must read like a senior engineer wrote it for a colleague. A doc page is allowed to be long, but use this voice:

- **Plain words over jargon.** Write for someone who knows the language but not this system. If a term is load-bearing, define it once in a sentence and then use it; if it's decoration, cut it.
- **No flourish.** No "seamlessly", "robust", "powerful", "leverage", "elegant", "under the hood", "it's worth noting that", "in today's fast-paced". No selling the feature — the reader already decided to use it. No exclamation marks.
- **Say the thing, then stop.** One idea per paragraph, two to four sentences. No paragraph that restates the previous paragraph in different words, no closing summary that repeats the page.
- **Concrete over abstract.** A short runnable example beats three paragraphs describing what the example would show. Real identifiers and realistic data, not `foo`/`bar`.
- **Lead with the sharp edges.** The things that actually cost someone an afternoon — the failure that looks like a bug but is a config error, the call that must happen first, the default that surprises — get their own headings or callouts. That's what makes a doc worth reading over the source.
- **No AI tells.** No emoji, no bold-lead bullet lists where every bullet is `**Word** — sentence`, no rhetorical questions as headings, no "Let's dive in", no tables of one-word cells padded to look thorough.
- **Never mention the workflow.** No phase names, no manifest, no backlog vocabulary. The reader is a user of the code, not a participant in how it got built.

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

Docs are written when the thing they document is settled — TESTING at the earliest, alongside the main PR. Documenting the happy path before TWEAKING ends means rewriting it. Where the project already has a docs site, follow its existing structure and register the page in the site's nav; a page nothing links to is a page nobody reads. Build the site once before committing to confirm it renders.

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
- Present **at least two distinct options** with concrete pros/cons — a real tradeoff matrix, not a strawman next to a favorite.
- Record the outcome in `architecture_decisions` (context, options, decision, rationale).
- Define `data_flow_description`: inputs, outputs, access patterns.
- Write the one-sentence `impact_target` and list `strict_scope_exclusions` (things explicitly NOT in v1).
- **Plan the test bed:** run `manifest.py tool list` and inventory what exists. Identify which registered tools this feature can reuse as-is, which need modification, and which new tools it will need — record the outcome in `test_bed_env` (e.g. "reuse seed-db and ui-shell; extend seed-db with a row-count knob; new: webhook-catcher"). TEST_BED then executes this plan instead of discovering it.

No implementation code in this phase. **Exit when:** major decisions are recorded and the user agrees on direction.

**On exit, ask the user** if they want the architecture doc generated: `manifest.py render <feature> --out <path>` produces a markdown summary (objective, scope, data flow, decisions, test bed plan) from the manifest. It's a generated artifact — regenerate rather than edit it, and never commit it.

### 2. HAPPY_PATH
Write the minimal code that delivers the impact target, and nothing else.
- **Forbidden:** try/catch (beyond what the language forces to compile), retry logic, input validation, config options, feature flags, abstractions for hypothetical reuse, logging beyond a couple of debug lines.
- If a forbidden thought appears ("what if the input is null?"), park it in `edge_cases` and keep going.
- Record entry points in `happy_path_entry_points`.

**Exit when:** the primary flow is code-complete against the recorded data flow. It does not need to be verified yet — that's what the test bed is for.

### 3. TEST_BED
Make the feature real and pokeable. The test bed is a **manual environment for the user** — they will personally click through it, test the ergonomics, and modify the driver script by hand. Build for them, not for automation. Two deliverables, always:

1. **A basic web UI** to exercise the feature interactively. Basic means basic: a single served HTML page (plain HTML + fetch is fine) with the inputs and outputs needed to try the feature and see what happens. If the feature has no UI surface of its own, build a thin page over its API. No framework, no build step, no styling beyond legibility.
2. **A minimal Python driver script** (e.g. `testbed/demo.py`) that demonstrates the **entire feature end-to-end** — the smallest script that does so. If demonstrating it requires standing up an HTTP server or a small REST API around the feature, the script does that too (stdlib or whatever the project already uses). Optimize for hand-editing: flat top-to-bottom flow, obvious variables at the top for the things the user will want to change (inputs, endpoints, example data), print what happens at each step. No argparse, no classes, no cleverness. Comment it heavily per the test bed exception in Comments & Commits — it's a guided tour the user will edit, not production code.

**Reuse before building:** execute the tool plan recorded in `test_bed_env` during ARCHITECTURE (run `manifest.py tool list` to refresh; if no plan was recorded, make one now). Adapt what exists instead of rebuilding it. Feature-specific scratch (this feature's `demo.py`, UI page, one-off data) lives in `testbed/scratch/<feature>/` and stays local.

**Modifying a registered tool:** registered tools are shared across features, so changes must stay generic. Extend via a new parameter or flag with the old behavior as its default — never hardcode this feature's data, endpoints, or assumptions into the shared tool. If the change only makes sense for this feature, copy the tool into `testbed/scratch/<feature>/` and modify the copy instead. After modifying a shared tool, update its registry usage with `manifest.py tool update --name <name> --usage "..."` if the invocation changed.

Also:
- Stand up the project's services (usually `docker compose up`; check the repo for an existing dev-environment convention first) and seed real, representative example data.
- **Record every command that matters** — start services, seed data, serve the UI, run the driver script — via `manifest.py testbed <feature> add --label ... --cmd ...` the moment it works. Reusing a label replaces its old command at the same position, preserving startup order; any older duplicate entries with that label are collapsed at their first position. New labels append. Remove obsolete commands with `manifest.py testbed <feature> remove --label "..."`, so a future session (or the TWEAKING loop) rebuilds the environment from `testbed list` alone. Use `test_bed_env` prose only for what commands can't capture.
- Drive the happy path end-to-end yourself once and report what actually happened, including failures, verbatim — then hand it to the user for manual verification.

**Exit when:** the UI and driver script both run, the happy path has been exercised at least once (working or not — a reproducible failure moves you to TWEAKING too), and the user has what they need to poke it themselves.

### 4. TWEAKING
Tight loop: change → run against test bed → observe → repeat. This loop is shared with the user — they iterate manually through the web UI and by editing the driver script; expect their edits and feedback to drive changes.
- Keep changes small and observable; verify each by re-running the recorded commands (`manifest.py testbed <feature> list`), not by reading code.
- Keep the UI and driver script working as the feature changes — they are the verification surface for the whole loop. Before touching `demo.py`, read its current contents immediately before editing and apply a targeted patch that preserves user changes. Scratch files are ignored by Git, so do not rely on `git diff` to detect their edits; do not regenerate the driver wholesale.
- Continue parking edge cases; the loop is for making the happy path *good*, not complete.
- Log any decision reversals in `architecture_decisions` (new entry, don't rewrite history).

**Exit when:** the user says the behavior feels right.

### 5. TESTING
Few tests, each one earning its keep.
- Prefer **one comprehensive integration test per flow** that exercises the same path validated in the test bed, over many mocked unit tests. Set `target_execution_path` to that flow.
- Each test should assert the things that would actually break: outputs, side effects, persisted state — list them in `required_integration_assertions` first, then write the test to cover them.
- Do NOT write tests for backlog edge cases yet.

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
| "I'll just add a quick try/catch while I'm here" | Park it. HAPPY_PATH forbids it; FINALIZATION consumes it. |
| "Let me write a test to check this works" | Before TESTING, verification happens in the test bed, by running it. |
| "This abstraction will help later" | Later hasn't been validated. Write the concrete version. |
| "I remember where we left off" | The manifest is the truth. Read it. |
| "I'll update the manifest at the end" | Sessions die. Update after each step. |
| "Let me commit this progress" mid-phase | Commits land at phase boundaries only. |
| "I'll fold the edge cases in before opening the PR" | The main PR is the happy path. Edge cases are follow-up PRs. |
| "The intro paragraph should sell the feature" | Docs are jargon-free and unflowery. State what it does, then stop. |
| "The plan doc should go in the repo" | Planning artifacts stay local. The code and its commit message are the record. |
