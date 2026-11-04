# Repository readiness

Map current instructions, canonical commands, prerequisites and affected contracts.
A request to inspect/readiness-check does not authorize installing tools, automatic
formatting, fixes, commits, live evaluations or deployments.

1. Inspect intended changed/staged scope, unrelated dirty work, authoritative
   documentation/configuration and affected behavior/tests/examples.
2. Preserve stable documented contracts, not incidental implementation structure.
   Profile-specific orchestration/storage/job contracts are not universal defaults.
3. Prefer an existing suitable local environment. Missing prerequisites are
   environment blockers unless a declared production dependency is actually absent.
4. Run mapped canonical checks under current permissions. Focused diagnostics do
   not replace required full checks. Inspect authorized auto-fixes and preserve
   unrelated work.
5. Distinguish patch-related failures, evidenced pre-existing failures and blockers.
   Fix/revalidate only when authorized. Do not weaken checks or bypass hooks.
6. Inspect final diff/staging for sensitive configuration, unintended changes,
   caches/state/build artifacts; never delete or unstage unrelated work.
7. Report scope, commands, results, fixes/automatic changes, findings and omitted
   checks. Local readiness is not deployed/live verification.

Use the [skills profile](../resources/profiles/skills.md), [template example](../resources/profiles/template.md)
or the target project's mapping. No duplicate validation script/engine is needed.
