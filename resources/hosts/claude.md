# Claude Code host mapping

Official reference: https://code.claude.com/docs/en/skills
Keep host settings separate from portable instructions. Do not add fork,
tool-preapproval, or explicit-only invocation settings without the corresponding
requirement. Manual use supplies observations; metadata alone does not.

Project-local skills reside in `.claude/skills/<name>/SKILL.md`. Keep the portable
method separate from host metadata and install complete ordinary folders. Do not
assert that analogous slash syntax or readable Markdown verifies invocation.

Inspect available subagent/model/context/waiting tools before selecting Debate.
Do not assume Codex tool names, OpenAI provider IDs, or follow-up capabilities are
available. Map actual peer handles, isolated contexts, follow-up messages/results,
concurrency accounting, and resume/cleanup capabilities to the selected Debate
method's lifecycle. Verify whether history survives closing or resuming a peer;
an initial spawn alone does not establish follow-up support. Workflow, ballot, and
recovery rules belong to that method; selection permissions belong to
[model policy](../models.md). Report unsupported required capabilities explicitly.

Test discovery, explicit/indirect invocation, parsing, helper resolution, permissions,
tooling and observed results in the actual host. A copied package or successful
file validation is only installation evidence. This repository has not yet run
the real Claude invocation/quality gates; that status must not be reported as passed.

Use [shared usage](../usage.md) for named controls, context, read-only help and
compatibility. Those forms are instruction grammar, not a new terminal router.
Helper data-preservation and package checks do not prove assistant/host selection;
observe routing only within separately approved evaluation scope.
