# Requirement and work-item coverage

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Use this mode for “reconcile these requirements against our tickets and code” or
“identify coverage and ownership gaps.” It produces a coverage register, not a
completion certificate, implementation task, or permission to change a tracker.

Establish authoritative requirements/use cases, decision dates, superseded/conflicting
decisions, declared scope and current work-item metadata. Exhaust relevant pagination
or label incomplete coverage. Absence from one repository is not absence elsewhere.

## Resolve authority and inspection scope

Record source ID/version/date/locator, which claims it governs, and its disposition:
current, superseded, historical proposal, or unresolved conflict. Newer text is not
automatically authoritative for every field. Definitions may come from an approved
specification, exact priorities from an inventory, and execution state from tracker
and implementation evidence. Retain superseded rows in the authority ledger without
double-counting requirements. A portfolio inclusion decision need not authorize
implementation inside an excluded product boundary; carry that conflict to its
owner, while reconciling unblocked requirements normally.

Record tracker query scope and pagination independently of code inspection. Include
relevant parent/child work and terminal/cancelled states; a filtered board is not
the entire backlog. Complete means the selected query's terminal page was reached
and all returned rows were inspected, not that all organizations were searched.
For saved sources distinguish “complete in supplied snapshot” from a fresh live
read. If a cursor/page/source is unavailable, record inspected pages/counts and
missing scope. Then classify an unseen delivery owner as unknown, not a proven
gap. In a complete declared inventory, “no adequate owner in this scope” is a gap,
still not proof of absence in an uninspected tracker or repository.

Map primary delivery, supporting/enabling work and validation separately. Distinguish
implemented baseline, requested increment, partial coverage, ownership gap and
unknown state. A broad use-case reference or related code is not completion.
Refine an appropriate existing owner before proposing duplicate work. Preserve
portfolio priorities without inventing tracker mappings.

## Build the register

Use one row per distinct requirement, with linked work-item roles and explicit
milestones when mixed priorities/scope warrant them. Include:

- Requirement ID/title, authoritative source/version/locator, exact source priority
  and current scope/conflict disposition.
- Implemented baseline and its code/test/artifact evidence; requested increment
  and which observable acceptance criteria are implemented, partial or unevidenced.
- Primary delivery owner; supporting/enabling items; validation owner/evidence.
  Preserve actual work-item type, status, parent and tracker priority separately.
- Dependencies/access/owner decisions; inspection completeness and unknowns;
  bounded existing-owner refinement or a clearly unfiled proposal where needed.

Do not force one item per requirement or call a shared engine the primary delivery
owner of every use case it enables. Done engineering foundations, sandbox proofs,
review sessions, production delivery and approved validation are separate claims.
Keep completed baseline history intact when new feedback asks for an increment.
An In Progress item can lack inspected implementation evidence; a To Do validation
item can have session evidence without an approved completion decision. Record
both rather than silently changing state.

Retain source priority values exactly, including fractional ranks such as `0.5`
and `1.5`, with their source meaning. Tracker `High`, `Unassigned`, roadmap labels,
effort and execution state are different fields. Never map a source rank into an
option, estimate, deadline or state without an approved mapping. Dependency work
may execute first without inheriting its consumer's priority.

Deliver a traceable register of requirement, source/version, owner, implementation
evidence, coverage/status, dependencies and unresolved decisions. Keep this report
separate from Iterate's CLI-owned feature backlog; no automatic state synchronization.
Default read-only. Authorized tracker edits use current metadata, preserve unrelated
values, exhaust necessary pagination and verify read-back. Do not collect sources
or construct research cohorts as a side effect. Historical proposals, even a later
note saying they were filed, grant no mutation authority and do not identify new
live keys without their verified mapping. Ask for an unavailable approved source
only if it blocks the requested conclusion; otherwise report the limitation.

Read [the complete reference and fictional register](backlog-worked.md) for a
concrete multi-source example and deterministic coverage boundary. Source `backlog`
is recorded in the bundled provenance resources. Report actual checks, remaining
unknowns and proposed follow-ups without claiming live refresh or model adherence.
