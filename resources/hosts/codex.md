# Codex host mapping

Project-local skills reside in `.agents/skills/<name>/SKILL.md`. Published packages
contain their complete resources. Symlinked local authoring folders may be used,
but portable installs copy ordinary folders and do not depend on the checkout.

Use actual tools exposed by the host; do not assume a particular tool namespace,
subagent schema or provider CLI. For Debate, preflight distinct-agent spawning,
model/effort selection, isolated initial contexts, concurrency, waiting/results,
and cleanup. Pass source access and scope explicitly. Map actual peer handles,
follow-up messaging, waiting/results, and resume/close capabilities to the selected
Debate method's lifecycle. Determine whether concurrency includes the parent and
whether closed peers retain resumable history. Do not assume these capabilities
from a successful initial spawn. Workflow, ballot, and recovery rules belong to
the selected Debate method; selection permissions belong to [model policy](../models.md).

`/develop`, `/review` and `/research` describe mode grammar, not a new executable
router. `$` or picker invocation is a host presentation detail. Explicitly test
selection/arguments and installed helper paths; metadata alone is not observed
invocation. Unsupported delegation leaves the Debate engine unavailable while
ordinary single-pass methods may remain usable. Model references do not imply
the model is actually available through this host.

Use [shared usage](../usage.md) for named controls, context, read-only help and
compatibility. Those forms are instruction grammar, not a new terminal router.
Helper data-preservation and package checks do not prove assistant/host selection;
observe routing only within separately approved evaluation scope.
