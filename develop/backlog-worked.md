# Fictional equipment coverage reconciliation

This fictional equipment case defines a complete selected inventory, requirements,
source priorities, ownership roles and inspection limits.

## Equipment stock monitoring

Request: reconcile alerting, expiry reporting, vendor onboarding and supplier
delivery acknowledgment against saved requirements, tracker pages and local code.
No tracker writes, source-data changes or new research are authorized.

### Sources and observed execution

- S1, approved stock specification v2, October 18: low-stock alerts, expiry report,
  vendor onboarding and supplier acknowledgment are distinct outcomes.
- S0, v1 appendix, September 2: emails for every movement; superseded by S1's
  approved threshold alerts. Do not count the old behavior as another requirement.
- P1, October 20 inventory: exact priorities alert=0.5, expiry=1.5, vendor=3,
  acknowledgment=2. These ranks are separate from tracker High/Low/Unassigned.
- D1, October 22 signed scope decision: vendor writes remain platform-owned;
  a same-day draft suggests doing them in this tool. Signed boundary is current;
  draft is an unresolved proposal, not authority to build or mutate records.
- J1, two saved tracker pages: first two rows, cursor `page-2`; second two rows,
  terminal cursor null. All four items inspected; complete **for this query**.
- C1, local synthetic inventory module: executes the shared engine and threshold
  selection. Expiry export and acknowledgment adapter are absent here. Supplier
  gateway repository is not supplied, so its implementation remains unknown.

The complete inspected C1 source is inert and self-contained:

```python
def normalize_stock(record):
    if type(record["sku"]) is not str or not record["sku"].strip():
        raise ValueError("stock identity required")
    return {"sku": record["sku"], "quantity": int(record["quantity"]),
            "threshold": int(record["threshold"]), "supplier_id": record["supplier_id"]}


def select_alerts(stock):
    return [record["sku"] for record in stock if record["quantity"] < record["threshold"]]
```

Normalizing `SKU-71` (quantity 2, threshold 5) and `SKU-72` (quantity 8,
threshold 5) preserves both canonical stock/supplier identities; selection returns
only `SKU-71`. This proves normalized stock and threshold selection, not dispatch,
expiry export, onboarding or delivery acknowledgment. No writes are performed.

| Item / type / parent | Saved state / tracker priority | Actual scope |
|---|---|---|
| STOCK-20 / Story / STOCK-1 | Done / Low | Shared normalized stock engine; supports alerting and expiry, not user-facing increments. |
| STOCK-31 / Story / STOCK-1 | In Progress / High | Primary threshold-alert owner; selector exists, notification dispatch/permissions incomplete. |
| STOCK-44 / Story / STOCK-1 | To Do / Unassigned | Primary expiry-export owner; code not evidenced. |
| STOCK-52 / Task / STOCK-1 | To Do / Low | Validation of alert/expiry outcomes; no approved validation result supplied. |

### Complete fictional register

| Requirement / source priority | Baseline / increment evidence | Primary; supporting; validation | Conclusion / next bounded step |
|---|---|---|---|
| STOCK-A threshold alert / 0.5 | Engine normalizes stock; selector returns low-stock records; notification dispatch absent. | 31; 20; 52. | Partial increment, existing owner. Finish dispatch under 31, preserve 20 Done and High tracker priority; access approval required. |
| STOCK-E expiry report / 1.5 | Same engine baseline; no expiry export in C1. | 44; 20; 52. | Partial foundation, requested increment unevidenced locally. Refine 44's export contract, not a new engine/ticket. Validation outstanding. |
| STOCK-V vendor onboarding / 3 | Engine reads supplier IDs; no vendor-writing contract demonstrated. | Primary unresolved outside tool; 20 enables data only; validation unknown. | Scope conflict/gap in inspected inventory; platform product owner must resolve boundary. Do not implement the draft or infer absence in the platform repository. |
| STOCK-R acknowledgment / 2 | Engine preserves supplier IDs; no routing or acknowledgment evidence. | No adequate owner in complete J1 query; support 20; validation unknown. | Ownership gap **in this inventory**; supplier gateway implementation unknown. Propose scope/owner clarification, not automatic adapter implementation. |

If page 2 is unavailable, STOCK-E's owner and STOCK-R's lack of owner become
**unknown**, not confirmed gaps. STOCK-A's inspected existing owner remains known;
its partial implementation does not become complete. Source priorities and saved
state stay unchanged under either inspection condition.

## Executable reconciliation boundary

This fixture takes already reconciled authoritative requirements; it does not
resolve a business conflict by last-modified time. Source provenance, priorities,
scope decisions, verified capabilities and uninspected locations are explicit
inputs. It distinguishes roles and owner completeness without any write boundary.
The caller obtains `verified` capabilities by executing the supplied inert local
modules, not by trusting an issue's Done label. All evidence claims are bounded to
those modules; this is not an automated proof of real-world feature completion.

Map inspected primary owners per increment criterion. Two separate owners of
selection and dispatch are `distributed`, not conflicting; two owners of dispatch
are `overlap`. An uncovered criterion is a `gap` only when the selected inventory
is complete, otherwise `unknown`. These aggregate states prioritize overlap,
then uncovered criteria, then one existing owner or distributed coverage.
`criterion_owners` retains sorted keys, including empty lists. Known coverage is
bounded to inspected rows; incomplete pagination cannot certify exclusivity.
An empty increment is invalid. Supporting/validation/cancelled items do not
supply primary ownership.

```python
def inspect_pages(pages):
    inspected = []
    expected_cursor = None
    for page in pages:
        if page["cursor"] != expected_cursor:
            raise ValueError("pagination chain mismatch")
        inspected.extend(page["items"])
        expected_cursor = page["next_cursor"]
        if expected_cursor is None:
            if page is not pages[-1]:
                raise ValueError("rows after terminal page")
            return inspected, True
    return inspected, False


def reconcile(requirements, pages, evidence):
    items, complete = inspect_pages(pages)
    if len({item["key"] for item in items}) != len(items):
        raise ValueError("duplicate work item")
    if len({requirement["id"] for requirement in requirements}) != len(requirements):
        raise ValueError("duplicate authoritative requirement")
    verified = set(evidence["verified"])
    register = []
    for requirement in requirements:
        identity = requirement["id"]
        baseline = set(requirement["baseline"])
        increment = set(requirement["increment"])
        if not increment:
            raise ValueError("increment criteria required")
        primary = sorted([item for item in items
                   if item["roles"].get(identity) in {"primary", "semantic_primary"}
                   and item["status"] != "Cancelled" and increment.intersection(item["scope"])],
                   key=lambda item: item["key"])
        supporting = [item["key"] for item in items if item["roles"].get(identity) == "supporting"]
        validation = [item["key"] for item in items if item["roles"].get(identity) == "validation"]
        criterion_owners = {criterion: [item["key"] for item in primary if criterion in item["scope"]]
                            for criterion in sorted(increment)}
        if any(len(owners) > 1 for owners in criterion_owners.values()):
            ownership = "overlap"
        elif any(not owners for owners in criterion_owners.values()):
            ownership = "gap" if complete else "unknown"
        else:
            ownership = "existing" if len(primary) == 1 else "distributed"
        missing = increment - verified
        coverage = "implemented" if not missing else "partial" if verified.intersection(baseline | increment) else "not_evidenced"
        if missing and (not evidence["local_complete"] or evidence["uninspected"]):
            elsewhere = "unknown"
        else:
            elsewhere = "not_evidenced" if missing else "not_needed"
        register.append({
            "id": identity, "source": requirement["source"],
            "source_priority": requirement["source_priority"], "scope_state": requirement["scope_state"],
            "baseline_implemented": sorted(baseline & verified),
            "increment_implemented": sorted(increment & verified),
            "increment_not_evidenced_here": sorted(missing), "implementation_elsewhere": elsewhere,
            "coverage": coverage, "ownership": ownership, "criterion_owners": criterion_owners,
            "primary": [item["key"] for item in primary],
            "supporting": supporting, "validation": validation,
            "validation_state": "approved" if identity in evidence["approved_validation"] else "unknown" if not validation else "outstanding",
            "tracker_priority": {item["key"]: item["priority"] for item in primary},
            "tracker_status": {item["key"]: item["status"] for item in items if identity in item["roles"]},
            "pagination_complete": complete, "dependencies": requirement["dependencies"],
        })
    return register
```

## Verification and limits

`tests/test_prompt_backlog_methods.py` executes the shared-engine/partial-increment
sources and this reconciliation function, checks complete and incomplete page
chains, existing ownership versus gaps/unknowns, exact priorities, validation and
no input mutations. Held-out domains/identities are independent of this example.
The tests check deterministic fixture behavior, not an agent's judgment of new
requirements. Current live keys, external implementations, approved validation
and model-mediated baseline/revision comparisons remain unperformed or unknown.
