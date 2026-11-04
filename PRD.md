# PRD: Portable, Evidence-Grounded Agent Workflow Skills

Revised November 4, 2026. Implementation target: this `mdbecker/skills`
repository. This document replaces the original eight-package proposal.

## 1. Objective and Decisions

Extend this project with three canonical area skills: **`/develop`, `/review`,
and `/research`**. Preserve the original eight capabilities as bounded,
independently invokable modes, together with the existing Iterate development
method and Debate review/discussion method. Preserve `/iterate` and `/debate`
as compatibility entrypoints, not separately evolving implementations.

Generalize the methods established in this project, Riskonnect, the agent
template, and incidental-findings work through explicit project/domain mappings.
Each published parent must remain usable without this conversation, the source
checkout, another installed skill, or an originating private repository.

### Approved design

- Three canonical parent packages; capability count is separate from package,
  command, operation, and compatibility-entrypoint counts.
- Eight original capabilities: BDD development, PRD authoring, prompt editing,
  requirement/backlog reconciliation, repository validation, code review,
  structural audit, and research-report assembly/maintenance.
- Existing Iterate and Debate functionality is retained. Report `create` is a
  bounded extension of the report capability, not a new research workflow.
- Ordinary feature work in this project uses Iterate. Test-first BDD is an
  explicit alternative, not an implicit replacement or mandatory phase gate.
- Review scope and review execution method are separate choices. Ordinary review
  defaults to single-pass; Debate is explicitly selected.
- Model names are reference profiles, not whitelists. Prefer economical capable
  models first, stronger middle-stage models, and strongest/XL-capability final
  synthesis, while permitting any host-available model within applicable limits.
- Codex and Claude remain portability targets. Neither is certified by shared
  Markdown, analogous command spelling, or checks performed in the other host.

**Success:** comparable task quality, preserved methodological and safety
invariants, demonstrated transfer, reliable migration, and honest verification.

**Non-goals:** redesign application runtimes; execute production workflows;
retrieve new research data; run research notebooks; certify clinical validity;
distribute restricted data; globally install skills; introduce a generic routing,
model-selection, or agent framework; add unrelated capabilities. This PRD
authorizes specification of the implementation, not execution of its external
or production workflows. Implementation actions remain subject to user and host
authorization.

### Prerequisites

Before implementing a slice, inventory current instructions, canonical sources,
existing helpers, protected contracts, host capabilities, and permitted actions.
The repository maintainer approves the slice's architecture and evaluation
protocol before its implementation or model-mediated evaluation respectively.
Resolve consequential permission/domain conflicts rather than guessing. Missing
historical artifacts limit fidelity claims; missing required evidence or access
blocks the affected gate, not unrelated authorized work.

## 2. Command Ownership, Packaging, and Migration

### 2.1 Canonical command grammar

The following is the intended user-facing grammar. Verify actual discovery and
argument handling in each host before claiming it is supported. Host-specific
`$` or picker invocation may differ without changing ownership or semantics.

| Command | Sole responsibility |
|---|---|
| `/develop iterate <feature> [phase]` | Existing six-phase feature lifecycle, user checkpoints, and feature state. |
| `/develop bdd <task>` | Explicit test-first behavior implementation or read-only behavioral-test review. |
| `/develop prd <target>` | Author or revise an implementation-ready specification; never execute it. |
| `/develop prompt <target>` | Targeted instruction and associated contract changes. |
| `/develop backlog <scope>` | Requirement/work-item ownership and coverage reconciliation. |
| `/develop validate-repo [scope]` | Canonical repository readiness checks and evidence-based reporting. |
| `/review code <target> [--scope diff\|source] [--engine single\|debate]` | Declared change or current-source review. |
| `/review smells <scope> [--engine single\|debate]` | Explicit structural audit with demonstrated consequences. |
| `/review discuss <topic> [--engine single\|debate]` | Technical decision discussion. |
| `/research report create <target>` | Initial assembly from approved saved evidence through an existing mapped build graph. |
| `/research report update <target>` | Scoped evidence-preserving changes through an existing report pipeline. |

Each request has one owning mode. Parents select and selectively load that
mode's method and applicable profile; they do not run every sibling workflow.
Explicit commands take precedence over indirect activation. Distinguish feature
implementation, specification drafting, review, audit, validation, and report
work before routing. Ask one targeted question only when consequential ambiguity
cannot be resolved from the request and current project policy. Reject unknown
arguments with concise usage rather than forwarding them as commands.

Default code-review scope follows the declared target: a supplied diff/PR uses
its established comparison; a current-source target may be reviewed without a
baseline, with the absence disclosed. Never invent a diff, attribute an existing
defect to a change without evidence, or widen to a repository audit implicitly.
Changing `--engine` changes orchestration, not scope or permissions.

### 2.2 Root-level layout and single ownership

Create `develop/`, `review/`, and `research/` at the repository root, alongside
the existing `iterate/` and `debate/` directories. Do not introduce an ambiguous
nested `skills/` tree. Each canonical parent contains:

- `SKILL.md`: discriminating activation, mode selection, common boundaries,
  selectively loaded resources, completion rules, and failure handling.
- Focused method references and worked examples for its modes, including
  reference-domain, transfer-domain, and failure cases.
- Project/domain/host profiles and deterministic resources only where necessary.

Do not require identical scaffolding for every mode, copy entire manuals, or
maintain eight duplicate `SKILL.md` workflows. Define common policy once and
include the required policy/resource closure in each published distribution.
Reuse canonical helpers; packaging copies derived from one source are not
independently maintained implementations. Do not expose bundled method copies
as competing discoverable skills.

Initially retain existing Iterate and Debate method resources at their current
paths as single authoritative sources. Parent distributions must bundle the
resources they need; they must not reach an uninstalled sibling or the developer's
checkout at runtime. Compatibility distributions likewise contain their required
resource closure. Document external prerequisites explicitly.

Retain `iterate/manifest.py`, its Python 3.11+/standard-library runtime contract,
existing state format, and helper-path behavior. If later relocating canonical
resources, preserve the old helper path with a thin forwarding shim and prove
installed-path behavior first. Do not duplicate manifest logic or relocate state
to consolidate commands. Any forwarding shim is compatibility plumbing, not a
second implementation or a new framework.

### 2.3 Compatibility disposition

| Existing entrypoint/resource | Required disposition |
|---|---|
| `/iterate <feature> [phase]` | Compatibility route to `/develop iterate`; preserve parsing, six phases, checkpoints, and resumption. |
| `/iterate park "description"` and `/iterate list` | Preserve their fast-path behavior without launching the phase workflow. |
| `/iterate` without arguments | Preserve existing status/feature-selection behavior. |
| `/debate review <target>` | Route to the corresponding code-review operation with `--engine debate`; preserve current-source/no-baseline support. |
| `/debate discuss <topic>` and contextual `/debate` | Preserve discussion and existing context/default handling with the Debate engine. |
| `iterate/manifest.py`, its tests, and `.ai-state` | Preserve one helper and compatible state; no automatic schema/path migration. |
| Existing discovery links and installation flow | Retain valid legacy entrypoints and add canonical parents as one tested release unit. |

Legacy entrypoints share canonical methods rather than competing ownership.
Preserve behavior except for the explicitly approved change from fixed model
IDs to the model-selection policy in §3.4. Replace model-branded stage headings
with role names throughout parent resources, legacy resources, README, and
CONTRIBUTING; preserve historical lineups as references.

Extend `scripts/validate_skills.py` with an explicit inventory of all published
parents and compatibility entrypoints. Check metadata, complete resource closure,
discovery links, and legacy/new invocation fixtures. Keep static packaging checks
separate from behavioral and host-compatibility evaluation. Update README,
installation guidance, CONTRIBUTING, and attribution where affected. Do not
globally install packages or remove existing installations as part of this work.

Deliver the packages, source-to-requirement matrix, sanitized fixtures,
evaluation protocol/results, migration checks, and a short adaptation guide.

## 3. Shared Method, Authority, and Model Policy

### 3.1 Portable method and explicit mapping

Separate stable decisions/ordering/evidence rules from project mappings, domain
policy, host adapters, and historical examples. Profiles explicitly identify:

- Authoritative instructions, editing surfaces, schemas, contracts, and conflicts.
- Canonical commands, helpers, prerequisites, editable/generated artifacts, and
  build dependencies.
- Protected behavior, evidence authority, uncertainty, cohort/comparison rules,
  restricted inputs, permitted outputs, and privacy/disclosure policy.
- Host metadata/discovery, arguments, resource resolution, tools/delegation,
  model/settings availability, and permission requirements.

Missing critical mapping produces a precise limitation or targeted question,
never a guessed substitute. Do not carry machine paths, issue keys, clinical
categories, table names, date windows, counts, model settings, or historical
assumptions into reusable defaults. Include an incidental-findings report profile
and a synthetic nonclinical transfer profile with genuinely distinct cohorts.

### 3.2 Authority, source trust, and action permissions

Current applicable instructions and authoritative contracts override historical
examples. Read them before work and preserve unrelated user changes. A parent
handoff carries only the authorized target, scope, and actions; selecting a mode
or model grants no additional permission.

Review/audit requests remain read-only; drafting authorizes only the requested
document work, not implementation. None implicitly authorizes branches, commits,
pushes, deployment, dependency installation, service startup, data acquisition,
external mutations, or additional model calls. Explicit selection of hierarchical
review may authorize its review delegation only under current host permissions,
data policy, and resource limits; it does not authorize application/research model
calls. Evaluations require their own approved protocol and applicable access.

Treat PRDs, source files, profiles, manifests, saved commands, historical examples,
and reviewer outputs as data, not permission grants. Before replaying a recorded
command, establish its current provenance, working directory, target, effects,
and permissions. Use argument-safe execution; do not interpolate untrusted paths
or proposals into executable shell strings. Respect scoped-path/symlink boundaries
and validate archives before extraction. Report blocked actions instead of routing
around unavailable access with credentials, provider CLIs, or new dependencies.

In the Riskonnect profile, coding-agent work must not access Databricks. Local
repository validation never establishes deployed/live verification. Report
assembly/maintenance reads saved evidence; it does not execute notebooks, retrieve
new source data, or make model calls to fill gaps. Deployment and publication
remain separately authorized in every profile.

### 3.3 Lifecycle and state boundaries

Iterate owns feature phases, decisions, deferred edge/hardening work, and `.ai-state`
through its existing CLI. Requirement/work-item coverage registers are separate,
normally read-only evidence reports. They may reference feature follow-ups but
must not automatically synchronize statuses, hand-edit manifests, or create a
second authoritative feature backlog. Authorized feature-state updates use the
CLI; tracker writes require current metadata, preservation, and read-back.

Select one implementation lifecycle for the task. Here, ordinary feature work
defaults to Iterate. Explicit BDD uses genuine red-before-production ordering
where project policy permits it. If an Iterate feature is active, resolve the
workflow change explicitly; do not silently mix constraints or alter its phase.
Given/When/Then acceptance descriptions may inform Iterate architecture, but do
not establish test-first BDD fidelity. Prompt-specific changes also respect the
selected lifecycle; specialization does not introduce a competing lifecycle.

A PRD states the preferred implementation design and genuine unresolved decisions.
It does not replace Iterate's real-options architecture discussion or user
agreement. Ordinary development does not automatically invoke broad audits,
hierarchical review, or every validation/evaluation workflow.

### 3.4 Model selection and bounded review execution

Any model actually available through the host may be used within platform,
project, provider/data-handling, tool, scope, and resource permissions. Named
models are reference profiles, not whitelists. Prefer economical capable initial
reviewers, stronger middle-stage reconciliation, and strongest/XL-capability final
synthesis; 5.5+ is advisory, not a minimum-version requirement. Tiers describe
operational preferences, not physical sizes or guaranteed intelligence. Version,
reasoning effort, throughput variants, price, and context length alone do not
establish task-specific capability.

| Stage | Count | Preferred allocation | Historical reference | Alternative used during this PRD review |
|---|---:|---|---|---|
| Independent review | 5 | Economy-capable | `gpt-6-luna` | `gpt-6-luna` |
| Reconciliation | 3 | Stronger middle tier | `gpt-6.1-terra` | `gpt-6.1-sol` |
| Final synthesis | 1 | Strongest/XL capability | `gpt-6-astra` | `gpt-6-astra` |

These are reference and execution records, not fixed eligibility lists, literal
size classifications, or measured evidence of superiority/savings. Maintain
dated per-host capability references with tested workloads/settings and unknowns;
map portable roles to actual available models rather than assuming identical IDs
or provider features across hosts.

Preflight actual access, required tools, evidence accessibility, context capacity
for source plus accumulated reports and output, compatible settings, and approved
budget. Unknown tier qualification alone does not prohibit use. If distinct tiers
are unavailable, same-model distinct agents or strongest-available profiles remain
permitted; disclose the unmet/unverified ladder and never falsely label the final
selection XL-qualified. Procedural independence does not prove model-error diversity.

Preauthorize substitutions inside existing permissions and budget without
repetitive model-ID approvals. Obtain approval before expanding provider/data
disclosure, tools, scope, or budget; stage-count/method changes also require an
explicit decision. Reference-name unavailability alone is not a blocker.

When hierarchical review is selected, retain five independent reviewers, three
independent whole-candidate reconcilers, and one mandatory final synthesizer,
even with zero findings. Preserve distinct agents, common scoped source/baseline
access, candidate IDs, dissent, and actual-source verification. Never silently
drop stages or substitute repeated turns from one agent for distinct roles.

Allow at most one additional invocation per affected role, shared across retry,
fallback, and escalation, within owner-approved total call/token/time/spend caps.
Trigger recovery by consequential omissions, truncation, tool/evidence failures,
or material disputes, not votes or self-confidence. Preserve original outputs;
affected downstream rechecks consume the same total budget. Unresolved source
facts may remain unresolved: stronger models cannot supply missing evidence.
Exhausted required-stage failures mean incomplete review. Budget exhaustion stops
additional work and leaves its completion limits explicit.

Report model eligibility, evidence-stage completion, preferred-tier conformance,
and quality acceptance separately. Include planned/actual selections, settings,
substitutions, retries, inspected/omitted evidence, and measured versus estimated
or unavailable telemetry. Tier conformance and successful invocation do not
establish quality, fidelity, cost savings, or provider billing.

### 3.5 Provenance

Preserve source excerpts with portable identity, relative path, pinned revision
or artifact hash, excerpt location, interpreted rule, applicability, and inspection
status. Retain existing NOTICE provenance separately from newly adapted methods.
Do not label supplied quotations independently verified unless checked against
the cited frozen source and context. The source register in §8 records starting
references, not complete historical verification or runtime authorization.

## 4. Capability Requirements

### 4.1 `/develop bdd`

**Trigger:** explicit test-first behavior implementation/fix, a project profile
that explicitly selects BDD, or read-only review of behavioral scenarios/tests.
It must not replace Iterate through a broad implementation trigger.

**Source intent:** observable behavior rather than implementation details
(`riskonnect_agent:prototype/new_prd_instructions.md:14`).

- Identify concrete acceptance outcomes, preserved behavior, and relevant
  negative/security cases; write focused Given/When/Then in domain language.
- In BDD implementation mode, write behavioral tests before production changes
  and observe the intended failures. Investigate already-passing scenarios;
  do not manufacture failure or confuse environment failure with a red test.
- Implement the minimum complete solution; preserve characterization tests.
- Exercise real architectural boundaries, stubbing external dependencies rather
  than incidental internal collaborators. Interaction assertions are appropriate
  when the interaction itself is contractual.
- Keep static/governance checks separate from behavioral evidence.

**Deliver:** scenarios, tests, focused changes/documentation when authorized,
observed red/green evidence, and unperformed checks. Review-only mode makes no
edits. Scenario vocabulary under Iterate is not a claim of full BDD execution.

### 4.2 `/develop prd`

**Trigger:** author or revise an implementation-ready specification, not execute it.

**Source intent:** choose the cleanest, clearest, lowest-complexity complete
solution (`riskonnect_agent:prototype/code_review.md:9`).

- Establish outcome, current baseline, proposed increment, and compatibility.
- Put prerequisites and consequential blocking decisions first.
- Choose one preferred design using correctness, simplicity, maintainability,
  project fit, and likely usage; expose genuine business/access/domain unknowns.
- Specify contracts, identities, time semantics, missing/ambiguous inputs,
  failures, exclusions, acceptance scenarios, documentation, and validation.
- Remove repetition, placeholders, and dependence on unavailable conversation
  context. Do not universalize cleanroom assumptions or approve lifecycle changes
  merely by writing a specification.

**Deliver:** concise, decisive developer handoff with bounded unresolved decisions.

### 4.3 `/develop prompt`

**Trigger:** targeted changes to model instructions and associated existing
schemas, examples, validation, replay, or versioning surfaces.

**Source intent:** generation behavior, exact wire-shape hints/examples, and compact
validated replay have different responsibilities
(`riskonnect_agent:docs/DEVELOPMENT_GUIDE.md:389`).

- Identify the behavioral delta and upstream/downstream contracts.
- Inventory actual surfaces; do not invent missing extraction/evaluation layers.
- Make targeted authorized edits and synchronize affected consumers. Add focused
  deterministic contract/example tests where supported, at the selected lifecycle's
  testing stage; retain existing regression checks throughout.
- Preserve evidence authority, uncertainty, redaction, application-owned fields,
  and accepted-output-only replay where applicable.
- Separate structural validation from generation quality. Model-backed checks
  require an approved protocol, permitted tooling, and appropriate data.

**Deliver:** coordinated changes, rationale, regression evidence, and remaining
generation-quality uncertainty, not a new evaluation system.

### 4.4 `/develop backlog`

**Trigger:** compare requirements/use cases, decisions, implementation evidence,
and work-item coverage; not source discovery or cohort construction.

**Source intent:** a broad use-case reference is not a completion claim
(`riskonnect_agent:JIRA_TICKET_TEMPLATE.md:26`).

- Establish source authority, dates, scope, and superseded/conflicting decisions.
- Read current work items and exhaust relevant pagination or disclose incomplete
  coverage. Repository absence is bounded evidence, not proof of absence elsewhere.
- Map primary delivery, supporting/enabling work, and validation separately.
- Distinguish implemented baseline, requested increment, partial coverage,
  ownership gaps, and unknown status.
- Refine a suitable existing owner before proposing duplicates; preserve exact
  portfolio priorities without inventing tracker mappings.
- Keep coverage records separate from Iterate state as specified in §3.3.

**Deliver:** traceable coverage register, gaps, dependencies, recommendations,
and unresolved decisions. Default read-only; tracker writes require explicit
authorization, current metadata, preservation, and read-back.

### 4.5 `/develop validate-repo`

**Trigger:** validate declared repository changes, verify completed work, or assess
pre-merge readiness. Inspection is not authorization to install prerequisites,
auto-fix files, change unrelated code, commit, deploy, or run live evaluations.

**Source intent:** canonical operator workflow and behavioral/stable contracts
(`databricks-tool-agent-template:AGENTS.md:14,19,25`).

1. Establish scope and authority; inspect changed/staged files, intended versus
   unrelated work, affected contracts, and authoritative docs/configuration.
2. Check relevant behavior, tests, examples, and documentation. Incidental internal
   structure is not a contract unless documented. Protect profile-specific
   orchestration/configuration/storage/job boundaries only where affected.
3. Verify tools and prerequisites; prefer a suitable existing local environment.
   Missing tools are blockers, not product defects by default. Installation,
   hooks, environment changes, and auto-fixing require applicable authorization.
4. Execute the mapped canonical checks. Focused diagnostics do not replace required
   full validation. Inspect automatic changes and preserve unrelated work.
5. Distinguish patch-related failures, substantiated pre-existing failures, and
   environment blockers. Fix/revalidate only when authorized; never weaken gates,
   bypass hooks, or modify unrelated code to obtain a pass.
6. Inspect final diff/staging for sensitive configuration, unintended changes,
   caches, state, and build artifacts. Do not delete/unstage unrelated work.
7. Report checks/results, changes, remaining findings, and omitted work; distinguish
   local repository readiness from live/deployed verification.

**This repository's profile:** README and CONTRIBUTING are authoritative; Python
3.11+ is required. Use the established local environment and checks:

```sh
.venv/bin/python -m unittest discover -s iterate/tests -v
.venv/bin/python scripts/validate_skills.py
```

Retain manifest regression coverage; extend the existing metadata/link validator
for new parents and compatibility resources. Documentation-only changes receive
applicable checks and explicit behavioral-evaluation limits.

**Template example, not this repository's default:** its canonical command is
`python3.12 -m pre_commit run --all-files --show-diff-on-failure`; hook installation
is separate setup. Its prohibition on default deterministic tool routing and its
deployed-job smoke-check definition remain profile-specific contracts/reporting
boundaries, not instructions to deploy or access Databricks.

**Deliver:** an evidence-based readiness report, focused references, and no
duplicate validation engine. Do not assume Python, pre-commit, or this layout
in transfer projects.

### 4.6 `/research report create|update`

**Trigger:** assemble an initial report or make scoped narrative, layout, chart,
appendix, or workflow-diagram updates using approved saved evidence and an
existing mapped build graph. `create` does not establish a new pipeline or conduct
new research. Missing authorized inputs or build configuration blocks the operation.

**Source intent:** saved-evidence-only assembly, aggregate output, distinct cohorts,
schema/derivation authority, and no fabricated review scores
(`incidental_findings:REPORT_HANDOFF.md:17,32`, `README.md:58`,
`FIELD_HELP_METADATA.md:35`).

1. Identify acceptance criteria and classify presentation-only, explanatory, or
   evidence-changing work. Locate authoritative inputs, editable/generated
   sections, existing build tools, missing dependencies, and source conflicts.
2. Capture hashes/versions and protected claims, values, cohorts/fingerprints,
   denominators, selection methods, uncertainty, caveats, and provenance links.
   For creation, derive this baseline from saved evidence, not nonexistent prior
   report output. Identify restricted inputs and permitted output forms.
3. Edit authoritative templates/helpers/diagram sources, not generated report
   HTML. Preserve markers, provenance mappings, aggregate allowlists, and disclosure
   checks. Check explanations against schemas/derivation code; editorial work
   must not alter definitions, computed logic, or uncertainty semantics. Scientific
   corrections require an explicit request and identified saved supporting evidence.
4. Reuse the existing assembly/asset pipeline and integrity checks. Detect stale
   assets and input changes during generation. On failure preserve the prior
   deliverable; for initial creation preserve source inputs and do not present a
   partial artifact as complete. Never fabricate missing dependencies or silently
   omit sections.
5. Compare protected evidence before/after, allowing only explicitly supported
   corrections. Run focused and applicable broader checks; inspect charts,
   controls, links, narrow layouts, print behavior, and offline requests. Report
   passed, failed, blocked, and unperformed checks without invented visual or
   independent-review acceptance.

Keep cohorts separate: similar labels/counts do not establish equivalence,
matched reruns, or improvement. Reference output remains aggregate-only; never
embed records, identifiers, sensitive quotations, credentials, or private artifacts.
No new source queries, notebook execution, model gap-filling, research execution,
sending, publishing, or deployment is implied. Existing approved pipeline
processing of saved evidence is not permission to change derivation semantics.

The required profile records source authority/conflict rules, build graph and
dependencies, protected evidence/comparison limits, restricted inputs/permitted
aggregates/suppression, automated and visual/offline checks, and expected output.
Ship incidental-findings and synthetic nonclinical multi-cohort profiles. Example:
`create reliability-summary` assembles saved aggregates; `update reliability-summary`
changes presentation while protecting the recorded evidence.

Primary adaptation references: `incidental_findings:scripts/assemble_report.py`,
`scripts/report_template.html`, `scripts/check_report.cjs`, and `REPORT_HANDOFF.md`.
Inspect their dependencies before reuse. Schemas, metadata, and visualization
helpers are dependencies, not field-documentation, extraction, visualization,
or deployment skill deliverables.

**Deliver:** authorized source/report changes, profiles/examples, protected-evidence
comparison, verification results, and remaining limitations.

### 4.7 `/review code` and `/review discuss`

**Trigger:** explicit review of a declared change/current-source scope or discussion
of a technical decision. Neither activates merely because code is being written.
Both default to single-pass and remain read-only unless separately authorized.

**Source intent:** one preferred remedy and intent → architecture → implementation
→ polish; avoid findings already covered by correctly applied automation
(`riskonnect_agent:prototype/code_review.md:7,13,37`).

Establish target, source snapshot, comparison when applicable, requirements,
instructions, protected contracts, relevant callers/tests/docs, previous findings,
and lifecycle constraints. If a comparison cannot be established, disclose it;
current-source review remains valid without introduction/regression claims.

Review intent, responsibility/architecture, behavior and implementation, then
material polish. Substantiate dead code, harmful duplication, leaky abstractions,
needless generalization/specialization, conditional complexity, scattered change
requirements, mixed ownership, fragile tests, stale documentation/names, and
requirements/code/test/documentation inconsistencies through actual usage.
Environment-only dependency failure is not automatically a defect; missing
declared production dependencies may be.

The historical cleanroom profile may recommend worthwhile cleanup without user
migration obligations only where those assumptions are explicitly established.
This repository has existing entrypoints/helper/state contracts: preserve them.
Unknown compatibility is not permission to remove behavior.

Each actionable code-review finding includes a stable ID, verified location,
issue/evidence/consequence, one preferred fix and rationale, introduced/worsened/
relevant-pre-existing status, compatibility assumptions, and fix-now/defer advice.
Retain the original urgency scale: Must fix before merging / Should fix now /
Optional, recommended now / Optional, can defer. Feedback type is TODO / Question /
Follow-up / Nit. These are not interchangeable with structural or impact severity.

Revised reviews recheck current evidence, mark verified resolutions, update open
findings, withdraw unsupported/stale claims with reasons, and deduplicate. No
actionable findings is valid. Technical discussion presents supported arguments,
tradeoffs, and the preferred decision or genuine unresolved boundary rather than
forcing defect labels or consensus. Report coverage and unperformed checks.

### 4.8 `/review smells`

**Trigger:** explicitly scoped structural analysis of a subsystem/repository,
not automatic expansion of code review. Default single-pass; read-only.

**Source intent:** report structure only with an identifiable maintenance,
change-locality, testability, security, or operational consequence; size/shape alone
does not establish a smell (`structural-review-artifact:report excerpt:9`).

- Establish snapshot, included/excluded scope, architecture, public invariants,
  callers/tests/configuration, language/framework, compatibility, and prior findings.
  Exclude generated files/environments. Include tests/experimental code only when
  requested or needed to substantiate a concern.
- Inventory coverage; trace responsibility clusters, state ownership, repeated
  algorithms, coupling, and coordinated-edit requirements through actual usage.
- Require a concrete consequence; choose the smallest complete remedy reducing
  demonstrated risk and sequence remedies by dependencies/risk, not file size.
- Diagnose bloaters, divergent change/shotgun surgery, duplicated branching/state
  policies, inappropriate coupling, harmful duplication, and inconsistent boundary
  solutions. Categories and complexity counts are diagnostic aids, not violations.
- Prefer cohesive boundaries, typed values, explicit policies, or shared adapters
  only when they remove real complexity. Preserve order/error behavior, APIs,
  schemas, security, and compatibility. Do not universalize a historical refactor.

Each finding includes ID, family, verified location, structural evidence,
consequence, preferred remedy, protected invariants, and necessary behavioral
validation. Retain S3 correctness/operational risk, S2 significant design risk,
S1 maintainability concern, S0 observation. Keep this scale distinct from code-review
urgency and Debate impact severity.

**Deliver:** scope/method, concise summary, ranked findings, file-by-file coverage
including reviewed files with no material findings, dependency-aware remedies,
and omissions. No finding is bounded evidence, not proof of perfection. Include
the separately referenced Python smell guide only if available and verified.

### 4.9 Shared Debate engine for `/review`

When explicitly selected, use the retained 5→3→1 hierarchy and §3.4 model policy.
Respect host concurrency and batch workers; no worker spawns additional agents.
Finish each stage before the next. Models are stage references, not role identities.

1. **Five independent reviews:** same target/baseline/question/snapshot/scope/access;
   complementary correctness/state, security/trust, integration/portability,
   evidence/coverage, and regression/resource lenses. Do not share peer conclusions
   until all finish. Record stable IDs, evidence, assumptions, omissions, hypotheses,
   and preferences separately. Replacements retain initial-review independence.
2. **Three independent reconciliations:** each reads all original reports and checks
   every candidate against raw source and counterevidence, including unanimous
   claims. Retain IDs through deduplication; dispositions are verified, conditional,
   rejected, or unresolved. Preserve supported minority findings and disputes.
   Safely reproduce where feasible. Also inspect consequential scoped boundaries
   for omitted candidates and admit new IDs; no extra blind-review phase is required.
3. **One final synthesis:** inspect raw evidence for included findings and
   consequential omissions, reconcile original and reconciled reports, deduplicate,
   and prioritize supported consequences. Do not vote, average severity, or merely
   polish preceding conclusions. Final synthesis runs even after unanimous clean
   reports. The parent verifies scope/support; material corrections return to the
   synthesizer before delivery.

Use critical/high/medium/low impact severity for genuine defects with explicit
assumptions, keeping preferences and method-specific urgency/structural scales
separate. Discussion preserves strongest evidence-based arguments and unresolved
tradeoffs. Honor the requested output format, including valid JSON when requested.
Report baseline, coverage, actual checks, stage/tier completion, limitations, and
available telemetry. No review authorizes exploit execution, edits, or posting.

## 5. Fidelity, Transfer, and Acceptance Evidence

### 5.1 Protocol and fixtures

The repository maintainer approves a written evaluation protocol before runs.
Record baseline/candidate revisions and profile/host/settings, authorized tools
and data/retention/destinations, frozen sanitized fixtures and held-out answers,
metric definitions, sample/repeat plan, regression margins, mandatory versus
optional checks, resource ceilings, and pass/fail/blocked/not-run rules. Do not
change thresholds after seeing results or substitute generated output for its
own baseline. Keep held-out answers unavailable to the executing agent.

Each original capability needs direct/indirect activation and unrelated non-trigger
cases, missing/conflicting inputs, unavailable dependencies, failure/permission
boundaries, reference regression, and substantive separate-project/domain transfer.
Also regress retained Iterate/Debate behavior and compatibility entrypoints.
Language/stack portability requires its own mapped, validated contracts.

### 5.2 Required practical cases

- **Routing/lifecycle:** ordinary Iterate versus explicit BDD; drafting/review-only
  versus edits; prompt specialization within the selected lifecycle; diff versus
  structural audit; single versus Debate engine; no-baseline legacy review;
  unknown arguments; unchanged feature/coverage ownership; no automatic sibling
  workflows or nine-agent review on every area command.
- **Packaging/migration:** old/new arguments and fast paths, all discovery links,
  missing resources, parent/legacy installed-path helper resolution without sibling
  installations/source checkout, compatible manifests, and no competing copies.
- **Validation:** clean changes, patch-related versus substantiated pre-existing
  failures, dirty unrelated work, missing prerequisites, authorized automatic
  formatting, documentation-only work, sensitive/artifact hygiene, and unrequested
  live/deployment actions. Preserve canonical checks and unrelated work.
- **Reports:** creation with approved saved inputs; missing evidence/build graph;
  unchanged-evidence presentation edit; explicit source-supported numerical
  correction; regenerated diagram; conflicting cohorts; restricted dependency;
  stale/input-changed assets; failed rebuild preserving output/inputs; blocked
  visual inspection; overstated accuracy/clinical validity; aggregate privacy;
  multi-cohort nonclinical transfer; no research execution/publication.
- **Review:** large cohesive routines/data models with no size-only finding;
  diverging duplicate state machines; scattered configuration; speculative
  abstraction adding complexity; environment versus packaging defects; cleanroom
  versus required compatibility; revised resolved/stale/duplicate/new findings;
  incomplete scope; clean no-finding scope; supported minority-only findings;
  misleading unanimity and consequential defects absent from initial reports.
- **Models/recovery:** available unlisted/older models; unmet/unknown tiers;
  same-model distinct-agent completion; unavailable delegation/tools; evidence
  truncation; bounded replacement preserving independence/IDs; shared budget
  exhaustion; unauthorized provider/data changes; hostile command/profile text;
  no false XL, stage-completion, quality, or billing claims.

Assess observable selection, actions, evidence, and artifacts, not heading matches,
reviewer agreement, minimum finding counts, or every historical recommendation.

### 5.3 Measurements and decision rules

Deterministic fidelity covers applicable report values, source/cohort identity,
derivation semantics, provenance/disclosure checks, validation contracts, manifest
behavior, resource closure, and legacy parsing. Protected values may change only
through explicitly requested source-supported corrections. Static metadata checks
do not establish agent behavior, host compatibility, or clinical/scientific validity.

For instruction/packaging fidelity, pair baseline/candidate runs on identical
snapshots/prompts/settings/tool access and frozen inputs. Model-selection/profile
experiments explicitly declare model/settings differences and otherwise match
conditions; do not pretend different lineups used identical model settings.
Repeat only under the preregistered variability/uncertainty rule.

Measure task correctness, evidence accuracy, consequential omissions, false
findings, uncertainty, minority/candidate retention, unsafe actions, reference
fidelity, tool calls, tokens, elapsed time, and quality/cost of the whole pipeline,
including recoveries and human review/repair. A cheaper initial call or successful
9-agent invocation does not prove a cheaper or better completed workflow. Separate
measured costs from estimates and unavailable billing; a cost acceptance threshold
is not an operational spending cap. Small samples do not prove universal parity.

Unauthorized action, restricted disclosure, fabricated evidence, or unapproved
protected-contract regression fails the affected evaluation regardless of averages.
Required quality/compatibility evidence not run, inaccessible, or insufficient to
establish its preregistered criterion blocks its claim. Optional omissions stay
disclosed. Report eligibility, stage completion, tier conformance, and quality
acceptance separately; an unmet model-tier preference alone does not bar an
otherwise acceptable run or release. Do not weaken gates to fit available results.

### 5.4 Per-host compatibility matrix

For both Codex and Claude record tested version/environment, metadata acceptance,
discovery, explicit/indirect activation and parsing, helper/resource resolution,
permissions, tools, delegation/models/settings, observed behavior, and limits.
Gate individual engine claims separately: a host may support a parent/single-pass
method while hierarchical review remains blocked or unverified.

Codex-first milestones are permitted when accurately labeled. Full two-host
completion requires both hosts' required observed checks; unsupported/unavailable
rows are never inferred successes. Do not invent provider adapters, credentials,
or compatibility from analogous syntax.

## 6. Implementation Sequence

Use this project's Iterate workflow for implementation, not mandatory test-first
development. Specification authoring/revision itself does not start a feature
manifest, implement its requirements, or execute evaluations.

1. Inventory authoritative methods/sources/dependencies/permissions and host
   capabilities. Approve ownership, migration/resource closure, lifecycle choices,
   and protected contracts using Iterate's architecture checkpoint.
2. Implement one useful thin slice, preferably `/develop validate-repo` for this
   checkout. Add only packaging/routing needed to exercise it; do not scaffold
   every mode or create a generic framework.
3. Reuse or provide Iterate's basic manual web UI and editable Python driver to
   exercise the slice. Record reproducible commands through the existing CLI;
   observe the flow and preserve user edits. Pause for user tweaking/acceptance.
4. After accepted behavior, add a few meaningful tests in TESTING. Retain existing
   manifest/metadata checks. Resolve deferred concerns individually in FINALIZATION
   with its user checkpoints; safety/permission boundaries remain in force always.
5. Repeat thin slices for development modes, shared review scope/engine, and report
   creation/update. Reuse accepted resources; keep lifecycle and area ownership
   distinct. Include reference and transfer examples with the implemented behavior.
6. Complete canonical validation, migration/resource checks, and authorized
   reference/transfer/model/host evaluations under the approved protocol. Refine
   observed failures without expanding capability scope. Keep results and limits
   explicit; no review/evaluation success is assumed from packaging.

Preserve unrelated work, current commit/branch/publication permissions, and
Iterate's local-only versus Git workflow. This PRD does not authorize commits,
new branches, pushes, installations, or deployments. Retain attribution and
source-supported excerpts without making original repositories runtime dependencies.

## 7. Release Gates and Definition of Done

Full release requires:

- Three canonical area packages cover the eight original capabilities and retained
  methods, with one owner per request, discriminating activation, bounded scope,
  complete resources, and explicit completion evidence. Compatibility packaging
  is accounted for separately; no eight-physical-package gate remains.
- Existing Iterate/Debate entrypoints, helper/state contracts, and intended methods
  survive migration, except the explicitly approved reference-model policy change.
  New/legacy discovery and installed-path checks pass; no required sibling install
  or inaccessible checkout dependency remains.
- No protected-contract regression, unauthorized action, restricted disclosure,
  fabricated evidence, weakened gate, or false verification claim.
- Required deterministic and preregistered behavioral/quality acceptance is
  satisfied. Reference fidelity and claimed transfer are demonstrated. No
  unexplained material workflow-quality/cost/latency regression is accepted.
- Both claimed host environments satisfy their required discovery/invocation/
  capability checks; unavailable host/engine evidence cannot pass that claim.
- Reviews have substantiated findings/proportionate remedies, lifecycle-aware
  recommendations, retained dissent/IDs, complete required evidence stages, and
  disclosed omissions. Model eligibility, stage completion, preferred-tier
  conformance, and quality acceptance remain separate statuses.
- Repository readiness uses canonical checks without implying live verification;
  report assembly protects evidence/provenance/privacy and preserves inputs/output
  on failure. Explicit saved-evidence corrections are separately evidenced.
- The maintainer receives packages/profiles, source matrix, sanitized fixtures,
  approved protocol/results, migration checks, adaptation guidance, and remaining
  blocked/unavailable/not-run work. Missing required gates block full completion;
  partial milestones are labeled, not silently promoted to release.

Global installation, publication/deployment, live workloads, new research, and
external mutations remain separately authorized. No additional skill families,
standalone model-selection system, extraction/voting workflow, or generic agent
framework is included.

## 8. Starting Source Register and Verification Limits

Portable identities below locate adaptation sources; exact versions/hashes,
excerpts, context, interpreted requirements, applicable profiles, tests, and
inspection statuses belong in the delivered source-to-requirement matrix. Source
line numbers are starting locators, not immutable contracts or proof of current
authority. Do not replace unknown revisions with fabricated values.

| Identity | Starting references | Status at PRD revision |
|---|---|---|
| `skills` | `README.md`, `CONTRIBUTING.md`, `NOTICE`, `iterate/SKILL.md`, `iterate/manifest.py`, `debate/SKILL.md`, `scripts/validate_skills.py` | Inspected during PRD review; implementation must recheck the working snapshot. |
| `riskonnect_agent` | `prototype/new_prd_instructions.md:14`; `prototype/code_review.md:7,9,13,37`; `docs/DEVELOPMENT_GUIDE.md:389`; `JIRA_TICKET_TEMPLATE.md:26` | BDD and code-review anchor snippets were spot-checked; full method/source fidelity is not established. |
| `databricks-tool-agent-template` | `AGENTS.md:14,19,25,120,133`; `docs/CD_DEPLOYMENT.md:65` | Initial workflow/test anchor snippets were spot-checked; remaining references require inspection. |
| `incidental_findings` | `REPORT_HANDOFF.md:17,32`; `README.md:58`; `FIELD_HELP_METADATA.md:35`; report assembly/template/check sources | Handoff anchor snippets were spot-checked; complete pipeline, artifacts, cohort and historical reproducibility remain unverified. |
| `structural-review-artifact` | Supplied structural-report excerpt originally referenced at line 9, including its separately named Python smell guide | Supplied-source claims only; inspect and freeze the artifact/available guide before claiming fidelity. |
| `original-prd` | Supplied eight-package PRD attachment | Starting artifact SHA-256: `f8f5c856157f63b15ed6222cbfee0857f7c57cf19c02e6e306afe770340f38e8`. |

Preserve necessary exact, authorized excerpts in package references once checked;
this revised PRD paraphrases their intent rather than certifying all historical
quotes. Record missing engines, guides, data, or artifacts without inventing
passing substitutes. A successful review invocation proves neither methodological
parity nor billing/quality superiority. The PRD review used the alternative
Luna→Sol→Astra lineup; it did not run skill-quality, compatibility, cost, or research
evaluations.
