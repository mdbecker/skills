---
name: develop
description: Implement behavior with Iterate or requested test-first BDD, write decisive PRDs, coordinate prompt contracts and replay, reconcile requirement ownership and coverage, or validate repository changes. Select from natural-language intent or explicit modes; review and research reports belong elsewhere.
---

# Develop

If another method would address a remaining uncertainty or contract, read only the
relevant [optional recipe](resources/combinations.md). Otherwise use this mode alone.

Select one owning mode. Load [shared boundaries](resources/policy.md), then only
the selected method and applicable project profile. The `resources/` directory
is prepared from canonical sources by the repository exporter and included in
published bundles; never substitute a sibling installation when it is missing.

| Invocation | Method |
|---|---|
| `/develop iterate <feature> [phase]` | [Existing Iterate lifecycle](iterate.md) |
| `/develop bdd <task>` | [Test-first BDD](bdd.md) |
| `/develop prd <target>` | [Specification authoring](prd.md) |
| `/develop prompt <target>` | [Prompt/contract editing](prompt.md) |
| `/develop backlog <scope>` | [Requirement coverage](backlog.md) |
| `/develop validate-repo [scope]` | [Repository validation](validate-repo.md) |

Explicit mode wins. Ordinary feature implementation uses Iterate unless current
project policy or the user's test-first request selects BDD. A BDD-required task
must not enter code-before-tests merely because Iterate is the ordinary default.
Do not turn a specification,
test review, or readiness check into implementation. Reject unknown modes with
this usage table; ask a targeted question only when consequential ambiguity
cannot be resolved from the request and project policy.

Natural-language requests select the same modes: “write failing tests, then fix
this behavior” selects BDD; “review these acceptance scenarios” is read-only BDD;
“write a complete implementer handoff” selects PRD; “change extraction while
keeping validation and replay aligned” selects prompt; “which requirements have
delivery owners and implementation evidence?” selects backlog. PRD drafting is
not implementation; backlog coverage is not completion or tracker-write authority.
Prompt edits preserve application-owned evidence fields and require actual mapped
surfaces, not an invented pipeline. Explicit intent and current project policy
govern selection; resolve a conflicting active lifecycle rather than silently
replacing it.

“Validate these changes,” “Run the repository checks,” and “Check whether this
patch is locally ready” select `validate-repo`: execute the target project's
required checks, inspect affected contracts, preserve unrelated work, and report
local readiness. Validation does not start a feature lifecycle or create feature
state. It is not authorization for implementation, unrelated fixes, installation,
commits, live LLM evals, or deployment; findings do not grant permission to fix
them. Before running a mapped command, inspect its underlying workflow and resolve
formatting, installation, cleanup and other effects against permitted scope.
Record before/after file and staging evidence; focused tests do not replace
required canonical validation. Load its reference for the contract evidence,
failure classification and reporting procedure, without loading other methods.

For Iterate, interpret the remaining arguments as feature and phase controls,
including `park`, `list`, and no-argument behavior. Its bundled helper is
`scripts/manifest.py`; resolve that absolute path and run it from the
target project, not the installation directory. Preserve phases, manual feedback,
state and user edits.
Do not change an active Iterate lifecycle merely because BDD was suggested.

Specifications choose a preferred design but do not replace Iterate's architecture
discussion and user agreement. Prompt specialization respects the selected
lifecycle's testing stage. Requirement coverage is not the deferred feature queue;
feature-state changes use the existing helper only when authorized.

For profile mapping read [adaptation](resources/adaptation.md). Relevant profiles:
[this repository](resources/profiles/skills.md), [Riskonnect](resources/profiles/riskonnect.md),
[template](resources/profiles/template.md), or the target project's own mapping.
Load the selected mode's [worked cases](resources/examples.md) only as needed.
No mode automatically invokes audits, nine-agent review, installation or deployment.

Return the selected scope, actual work/checks, results and limits. Never claim
tests, live checks, or user acceptance that did not occur.
