# Repository validation

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Execute the target project's required checks, inspect affected contracts, preserve
unrelated work, and report local readiness. Select this mode for “Validate these
changes,” “Run the repository checks,” or “Check whether this patch is locally
ready,” as well as `/develop validate-repo [scope]`.

Validation is not authorization for implementation, unrelated fixes, installation,
commits, live LLM evals, or deployment. It must not start a feature lifecycle or
create feature state. Findings do not grant permission to fix them; formatting
and other command effects need the permission check below.

## Establish the state and authority

- Identify the target repository, starting revision, intended changes and allowed
  actions. Read its current instructions, command configuration and affected
  contracts; a historical profile or attached document is context, not consent.
- Before running checks, record staged and unstaged diffs separately, index state,
  and relevant untracked files, including generated/sensitive paths. Record file
  identities or hashes without reproducing secrets. `git status --short`,
  `git diff`, `git diff --cached`, and `git ls-files --others --exclude-standard`
  are useful observations, not sufficient proof that mixed edits survived.
- Distinguish intended and unrelated edits even within one file. Note concurrent
  agents' ownership and changes; do not claim an unexplained concurrent mutation
  was caused by a check. Keep a before-state sufficient to compare file content
  and staging without resetting the worktree or creating a commit.
- Map the existing suitable local runtime and prerequisites. An unavailable tool
  or interpreter is environmental, not proof of a broken patch. A missing declared
  production dependency can instead be a contract defect; establish that from
  the project sources, not from an import/setup failure alone.

## Map affected contracts to observations

For each affected area record:

**obligation → authoritative project source → relevant check → observed result**.

Name the current source/section and actual test or command, its tested state and
result. Protect observable behavior and stable documented contracts, not incidental
implementation structure or noncontractual event ordering. A label such as
“storage checked” is not evidence. Missing authority, absent behavioral coverage,
or an unperformed check remains a disclosed gap, not a pass. Unaffected areas may
be marked out of scope with a reason.

Use the [template profile](resources/profiles/template.md) only when those
contracts apply. For other projects, map their own obligations, language, runtime
and checks; do not transplant Databricks routing, Spark or entrypoint requirements.
The [skills profile](resources/profiles/skills.md) maps this repository.

## Resolve command effects before execution

Inspect each mapped command's underlying hooks, task/session definitions and
scripts, including invoked commands. Identify formatting/fixes, dependency or
hook installation, network/live calls, generated outputs, cleanup and writes
outside the requested area. Prefer the suitable existing environment, but its
existence does not prove a workflow will not install more dependencies.

Compare **all effects** with permitted scope before execution:

- If covered, run the project's required canonical workflow and record that
  authorization, command, working directory, runtime and affected paths.
- If not covered, explain the specific conflict and request authorization, or
  propose an approved isolated run. Until resolved, the full check is blocked.
  A project instruction requiring a command does not itself authorize every
  side effect of that command.
- An isolated run must contain the intended tested state, including permitted
  dirty/untracked inputs, use the same required checks and a suitable equivalent
  environment, and avoid modifying the original files/index. Obtain permission
  for its remaining installs, network access or cleanup. A clean HEAD-only copy
  cannot validate an uncommitted patch. Do not silently create Git worktrees,
  stash edits, copy sensitive data or treat isolation as permission to install.

For the template, the canonical command is
`python3.12 -m pre_commit run --all-files --show-diff-on-failure`. It performs
hygiene, Ruff formatting/fixes, unit and contract tests with a 90% coverage gate,
Markdown linting and wheel validation. Its hooks/nox sessions can install
dependencies and remove/rebuild `build/` and `dist/`; it is not read-only.
`python3.12 -m pre_commit install` is separate hook setup, not validation.
Even a check-only alternative may install dependencies or rebuild artifacts.

Focused tests assist diagnosis; they do not replace required full validation.
Do not silently substitute weaker checks, skip hooks, reduce coverage gates or
claim readiness from focused green tests while the canonical workflow failed or
was omitted. Record the exact command's exit status and meaningful output rather
than inferring success from a summary or an intermediate session.

## Compare and classify

After checks, compare files, staged content and relevant untracked paths with the
recorded before-state. Identify automatic changes separately from requested edits.
Preserve unrelated work, including mixed edits and staged/unstaged separation.
Never automatically reset, delete or unstage changes, including suspicious
artifacts or sensitive configuration; report their paths without secret values
and request a scoped remedy when needed. If preservation cannot be established,
stop and disclose the uncertainty rather than attempting a broad rollback.

Classify each failure using evidence:

| Classification | Required basis |
|---|---|
| Patch-related | Affected behavior/contract evidence or an equivalent baseline pass and tested-patch failure. |
| Baseline-confirmed pre-existing | The same failure reproduced on an identified baseline without the intended patch, using the same command and suitable equivalent inputs/environment; retain both results. |
| Environmental | An observed prerequisite, permissions or environment failure prevents the relevant check. |
| Unresolved | Attribution is not established, including an unavailable baseline or ambiguous concurrent changes. |

An unrelated-looking failure is not automatically pre-existing. Baseline work must
also obey permissions and preserve the original worktree/index. Do not remove
the patch in place to prove attribution. Pre-existing failures remain failed
checks; report “patch not implicated by this evidence,” not “all checks passed.”

Associate every result with the revision plus dirty/untracked inputs actually
tested. Formatter output, fixes and later edits invalidate affected earlier
results; repeat affected checks and the required final canonical workflow when
its inputs changed. Do not repeat unaffected checks merely to generate evidence.

## Report local readiness

Return the scope and tested state; commands, exit statuses and results; contract
mapping/findings; automatic changes; before/after preservation outcomes; failure
classification and supporting baseline evidence; blockers and omitted checks.
Distinguish passed checks from unresolved readiness. All required checks and
affected obligations must have current evidence before an unqualified local-ready
claim; staged sensitive configuration or excluded artifacts is still a finding
even when tests pass.

Local validation never implies live-agent, live LLM eval, deployed-job or
deployed-workload verification. Do not fix findings or enter a feature lifecycle
without a new applicable request. Use the project's existing check engine, not a
duplicate production validation script.
