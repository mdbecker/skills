---
name: develop
description: Implement behavior, revise implementation specifications or prompts, reconcile requirement coverage, or validate repository changes through explicitly selected development modes. Reviews and research reports belong to their own areas.
---

# Develop

Select one owning mode. Load [shared boundaries](resources/policy.md), then only
the selected method and applicable project profile. The `resources/` directory
is prepared from canonical sources by the repository exporter and included in
published bundles; never substitute a sibling installation when it is missing.

| Invocation | Method |
|---|---|
| `/develop iterate <feature> [phase]` | [Existing Iterate lifecycle](resources/iterate/method.md) |
| `/develop bdd <task>` | [Test-first BDD](references/bdd.md) |
| `/develop prd <target>` | [Specification authoring](references/prd.md) |
| `/develop prompt <target>` | [Prompt/contract editing](references/prompt.md) |
| `/develop backlog <scope>` | [Requirement coverage](references/backlog.md) |
| `/develop validate-repo [scope]` | [Repository validation](references/validate-repo.md) |

Explicit mode wins. Ordinary feature implementation uses Iterate unless current
project policy explicitly selects another lifecycle. Do not turn a specification,
test review, or readiness check into implementation. Reject unknown modes with
this usage table; ask a targeted question only when consequential ambiguity
cannot be resolved from the request and project policy.

For Iterate, interpret the remaining arguments as the existing `/iterate` arguments,
including `park`, `list`, and no-argument behavior. Its bundled helper is
`resources/iterate/manifest.py`; resolve that absolute path and run it from the
target project, not the installation directory. The copied method's directory
is its helper directory. Preserve phases, manual feedback, state and user edits.
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
