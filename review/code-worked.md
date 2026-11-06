# Complete code review and revised review

Synthetic fictional order-import example. This is an illustrative deliverable,
not an instruction to edit the example or a previously executed agent review.
Line locations count from the first line of each code block. The independent
evaluation uses different artifacts and does not receive this report as an answer.

## Supplied contract and snapshots

Request: “Review the name-selection change, then consolidate your review after
the supplied revision. Read-only; assess intent, architecture, implementation and
material polish.” The catalog is a complete in-memory list of eligible orders.
Trim and case-fold full labels; no fuzzy selection. Deduplicate repeated rows with
one canonical `id`; multiple distinct IDs are terminal ambiguity with no queue
write. Only canonical IDs cross the queue boundary. Preserve `submit_order`, used
by an existing client. No cleanroom assumption is established. Installation of
the optional production queue client is unavailable in this review environment.

Earlier `importer.py` (the real comparison base):

```python
def submit_order(order_id, queue):
    return queue.submit(order_id)
```

First submitted `importer.py`:

```python
def submit_order(order_id, queue):
    return queue.submit(order_id)


def submit_by_label(label, orders, queue):
    matches = [order for order in orders if order["label"].casefold() == label.strip().casefold()]
    if not matches:
        return {"status": "not_found"}
    selected = matches[0]
    return submit_order(selected["label"], queue)
```

`client.py`:

```python
from importer import submit_order


def confirm(order_id, queue):
    return submit_order(order_id, queue)
```

First submitted `IMPORT.md`:

```text
Submit an eligible order using its full label.
Any failure means the order does not exist; retry with a different label.
```

`contract_tests.py` contains acceptance scenarios but cannot execute the installed
production queue client here; the inert list-backed queue reproduction below is
available. No production dependency declaration or packaging diff was supplied.

## First review — complete output

Scope: the supplied `importer.py` diff and `IMPORT.md`, with `client.py` as caller
evidence and the stated acceptance contract. Not a repository audit.

1. **Intent:** full-label lookup is the requested increment; preserve canonical
   identity and existing direct-ID submission. No speculative selector framework.
2. **Architecture:** the existing write seam is appropriate, but R01 crosses it
   with the wrong identity. The public forwarding API has a real consumer; do not
   remove it as “dead code.”
3. **Implementation:** R02 arbitrarily resolves multiple IDs. A no-match outcome
   already returns without writing. Missing-client setup is not a product finding.
4. **Material polish:** R03's operational instructions misclassify infrastructure
   failures and can encourage inappropriate resubmission; not a formatting nit.

### Ranked findings

**R01 — Wrong identity crosses the write boundary**
- Location: `importer.py:10`; contract and `client.py:5` require canonical IDs.
- Evidence: the new path passes `selected["label"]`; direct submission passes an ID.
  For `{id: "order-7", label: "Restock"}`, the queued value is `Restock`.
- Consequence: a queue consumer cannot reliably locate the order; names may repeat.
- Preferred complete fix: pass the resolved canonical `id` through the existing
  `submit_order` boundary, and test the queued ID for both direct and label paths.
- Rationale: repair boundary semantics once, without changing the queue interface
  or adding label resolution downstream. Preserve queue error propagation.
- Urgency/type: **Must fix before merging / TODO**. **Fix now**: identity corruption
  blocks the requested behavior. Introduced by the supplied new path.
- Compatibility: preserve the public `submit_order` signature. Even established
  cleanroom would not excuse the identity error; it could only alter obsolete APIs.

**R02 — Duplicate names select arbitrarily**
- Location: `importer.py:9`, supported by matching at line 6.
- Evidence: two eligible rows with label `Restock` and IDs `order-7` and `order-8`
  produce two matches; index zero is selected. Reversing rows changes the target.
- Consequence: a human-readable selector can submit the wrong order.
- Preferred complete fix: collect distinct canonical IDs for the exact normalized
  label; return `ambiguous` without writing when there is more than one; submit
  the unique ID when repeated rows refer to the same record. Test both row orders,
  same-ID duplicates, case/whitespace matching and no-match with no write.
- Rationale: one small uniqueness check implements the explicit grouping contract;
  sorting, fuzzy ranking or “first wins” only hide ambiguity.
- Urgency/type: **Must fix before merging / TODO**. **Fix now**: arbitrary selection
  violates acceptance. Introduced in the supplied diff.
- Compatibility: the new label path may return a controlled ambiguity outcome;
  keep direct-ID behavior and actual queue errors unchanged. Cleanroom is irrelevant.

**R03 — Failure guidance encourages the wrong recovery**
- Location: `IMPORT.md:2`; `submit_order` propagates queue failures at line 2.
- Evidence: the documentation calls *any* failure not-found, while a queue failure
  is distinct from lookup's explicit `not_found` result.
- Consequence: operators may alter a valid selector after infrastructure failure
  and accidentally submit a different order.
- Preferred complete fix: document `not_found`, `ambiguous`, accepted submission
  and propagated queue failure separately; instruct ambiguity resolution by ID,
  and infrastructure recovery under the queue's existing retry policy.
- Rationale: a compact outcome table fixes meaning without adding another retry
  mechanism or duplicating the queue implementation.
- Urgency/type: **Should fix now / Nit**. **Fix now** in this revision: a small
  documentation correction materially affects safe use. Introduction unknown
  because no documentation base was supplied.
- Compatibility: no API change; the recommendation is independent of cleanroom.

**R08 — Catalog labels are not normalized at the comparison boundary**
- Location: `importer.py:6`; the supplied contract requires trimming full labels.
- Evidence: `{id: "order-7", label: " Restock "}` queried with `Restock` returns
  `not_found` because only the requested label is stripped.
- Consequence: a valid normalized match is missed; catalog whitespace can also
  hide a distinct-ID ambiguity.
- Preferred complete fix: strip and case-fold both compared labels, retaining
  canonical-ID deduplication and ambiguity/no-write behavior.
- Rationale: honor the declared normalization at both input boundaries, without
  assuming a pretrimmed catalog or adding fuzzy matching.
- Urgency/type: **Should fix now / Follow-up**. **Fix now**: the name-selection
  contract is incomplete. Introduced by the supplied new path.
- Compatibility: preserve the direct-ID facade, result shapes and queue failures.

Coverage: both finding-scope files fully inspected; caller fully inspected as
supporting evidence; acceptance scenarios inspected, production-client runtime
blocked; other repository files outside scope. Source and inert queue traces can
support findings; installation, live queue checks and generation quality are not
run. No edits, installs or posting authorized. No finding quota.

## Supplied revision and prior-report correction

Revised `importer.py`:

```python
def submit_order(order_id, queue):
    return queue.submit(order_id)


def submit_by_label(label, orders, queue):
    identities = {order["id"] for order in orders if order["label"].strip().casefold() == label.strip().casefold()}
    if not identities:
        return {"status": "not_found"}
    if len(identities) > 1:
        return {"status": "ambiguous"}
    return submit_order(next(iter(identities)), queue)
```

`IMPORT.md` is unchanged. The supplied prior review also includes R04 (“queue
client missing implies production defect”), R05 (“direct-ID wrapper is unused”),
R06 (“ambiguous orders are arbitrarily submitted”), and R07 (an unrelated exporter
cleanup outside this revised scope). Those claims must receive dispositions;
they are not facts merely because a prior reviewer stated them.

## Consolidated revised review — complete output

Scope/snapshot: revised importer and unchanged import docs, compared with the
first submitted sources above; same compatibility and permissions. Revisit intent,
architecture, implementation and material polish in that order. Intent and seam
placement remain appropriate. The canonical-ID and ambiguity corrections resolve
the two blockers; two-sided normalization also resolves R08. Documentation still
needs its supported correction.

| Prior ID | Disposition | Current evidence |
|---|---|---|
| R01 | Resolved | `importer.py:11` passes the unique canonical ID through the preserved boundary. |
| R02 | Resolved | Lines 6–10 deduplicate IDs and return ambiguity before a write. |
| R03 | Open, unchanged urgency/type | `IMPORT.md:2` still conflates lookup outcomes and queue failure. |
| R04 | Withdrawn | No missing production declaration is evidenced; only this review environment lacks the client. |
| R05 | Withdrawn | `client.py:1,5` imports and invokes the required public API. |
| R06 | Merged into R02 as alias, now resolved | Same distinct-ID ambiguity consequence, not a second finding. |
| R07 | Not reassessed | Exporter is outside the declared revised scope; no claim of a fix. |
| R08 | Resolved | `importer.py:6` strips and case-folds both catalog and requested labels; padded catalog matches preserve canonical identity and distinct-ID ambiguity. |

Only open actionable finding: **R03**, at `IMPORT.md:2`, **Should fix now /
Nit**, fix now for the operational consequence above. Preferred complete
fix/rationale/compatibility remain exactly as stated in the first review; no new
open findings are supported. A revised report consolidates rather than appends.

Verification reproduced by repository tests using an inert queue: first sources
queue a label and choose an arbitrary duplicate; revised sources queue `order-7`
for a unique/same-ID match, write nothing for missing/distinct-ID matches, preserve
direct-ID submission, and propagate queue exceptions. These traces are local
example checks, not executed production-client tests or independent agent output.

Limits: no real host/model evaluation, installation, external queue or repository
audit; uninspected areas remain excluded. Reviewer recommends, authorized developer
edits. No claim that packaging success establishes review quality.
