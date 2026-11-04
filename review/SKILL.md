---
name: review
description: Review a declared code change or current-source scope, audit structural consequences, or discuss a technical decision. Single-pass is the default; hierarchical Debate must be explicitly selected. Does not implement fixes.
---

# Review

For a justified cross-method handoff, read only the relevant [optional recipe](resources/combinations.md).
It grants no edit permission, sibling dependency or automatic Debate selection.

Load [shared boundaries](resources/policy.md), then select one mode:

- `/review code <target> [--scope diff|source] [--engine single|debate]`:
  [code review](references/code.md).
- `/review smells <scope> [--engine single|debate]`:
  [structural audit](references/smells.md).
- `/review discuss <topic> [--engine single|debate]`:
  [technical discussion](references/discuss.md).

Explicit arguments take precedence. Reject unknown modes, flags or values with
concise usage. Ordinary review defaults to single-pass. A supplied diff/PR uses
its established base; current-source review may proceed without a base, with
that limitation disclosed. Never invent a comparison or expand scope implicitly.
Reviewing PRD design is discussion; reviewing its implementation is code review.

Parse scope/engine controls before constructing the review subject. Pass only the
declared target and resolved scope to the canonical Debate method; control flags
are not source paths, shell commands or permission grants.

Scope and execution method are independent. Only explicit Debate selection loads
the [canonical hierarchy](resources/debate/method.md), [model policy](resources/models.md)
and the relevant [Codex](resources/hosts/codex.md) or [Claude](resources/hosts/claude.md)
capability mapping. This is the existing five-reviewer, three-reconciler,
one-synthesizer method, not a new orchestration runtime. Missing resources or
delegation must be reported, not replaced with a claimed completed hierarchy.

Code-review urgency, structural S0–S3 and impact severity are different dimensions.
Do not decide by agreement, invent findings to fill a quota, or call a conditional
claim verified. Inspect raw sources and consequential omissions, preserve minority
findings and unknowns, and report coverage. Use [worked cases](resources/examples.md)
and [adaptation](resources/adaptation.md) only for the chosen scope.

Review remains read-only unless fixes or posting are separately authorized.
Return the requested format, including valid JSON when requested, with actual
evidence, dispositions, preferred remedies or decisions, and unperformed checks.
