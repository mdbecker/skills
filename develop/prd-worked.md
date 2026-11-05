# Worked PRDs: decisive, bounded handoffs

These complete synthetic handoffs need no earlier conversation or inaccessible
source repository. The Python blocks are executable design illustrations for
checking the specified contracts, not deployed implementations. Drafting these
PRDs does not authorize implementation, tracker writes, model calls or deployment.
Select the relevant example; the event fields are not fictional defaults.

## Fictional PRD: select a catalog event by name

### Prerequisites and blocking decisions

Confirmed **for this example**: the existing authenticated application supplies a
complete tenant-scoped event catalog; every entry has one unique canonical `id`
and a nonblank display `name`. The existing submit API already accepts canonical
IDs and checks authorization/catalog membership again at submission. Names are
not unique. This increment has no new evidence acquisition or access policy.

No owner decision remains open under these assumptions. If the live project's
tenant/access scope is unknown, the access owner must confirm the permitted catalog
before name lookup can ship. If canonical ID authority is unknown, the domain
owner must identify it before resolution can be implemented. Do not replace
either decision with a global search, a generated ID or a guessed permission.
Normalization, ambiguity handling and error shapes below are resolved technical
choices, not questions to leave to the developer.

### Outcome, baseline and increment

Users can enter an event's human-readable name without losing its canonical
identity or accidentally selecting another identically named event. Baseline:
ID-based selection/submission works; names are display-only. Increment: add one
name resolver and a disambiguation state in the existing selection UI. Preserve
the ID path, existing submit validation, payloads and receipt/error contracts.

### Preferred design and interfaces

Use a pure resolver over the application's existing scoped catalog snapshot.
Return the catalog's exact ID/name, never a name-derived ID. This adds a single
boundary before the existing submit facade, avoiding a second registry, fuzzy
matching, a model call or a persistence/schema migration. A linear scan is
sufficient for the supplied bounded catalog; no new index/cache is justified.

`resolve_event(selector, catalog, complete)` returns one of the JSON results
below. `selector` contains `id`, `name`, or both, and no other keys. Supplied values
must be nonblank strings. IDs compare exactly, case-sensitively, without trimming
or coercion. Names compare with `strip().casefold()` only; no fuzzy, accent or
punctuation removal. The returned name is the authoritative catalog spelling.

| Condition | Result | UI / write behavior |
|---|---|---|
| Unique ID, or exactly one name match | `selected`, `event: {id, name}` | Enable existing confirmation; no resolver write |
| Multiple name matches | `ambiguous_name`, all `candidates: [{id, name}]` sorted by ID | Show choices; require explicit canonical ID; never pick first |
| Neither input supplied | `missing_input` | Request ID or name; no submission |
| Null/blank/non-string value or unknown key | `invalid_input` | Correct input; no submission |
| ID/name not found | `not_found` | Correct input or refresh catalog; no submission |
| ID exists but supplied name disagrees | `id_name_mismatch` | Reconfirm authoritative selection; do not silently ignore name |
| Incomplete/unavailable snapshot or malformed/duplicate ID entries | `catalog_unavailable` | Disable confirmation; refresh/fix upstream; never infer absence or uniqueness |

All results use `status` with those exact lower-case values; only selected and
ambiguous results carry `event` or `candidates`. Failure results never carry a
selection. Snapshot ordering is not a tie-breaker. Authentication remains upstream
and submission authorization remains downstream; resolver output is not an access
grant. A deleted/inaccessible event at confirmation uses the existing submit
failure and requires refresh, without name substitution or automatic retry.

### Executable reference design

```python file=event_selection.py stage=design
def resolve_event(selector, catalog, complete=True):
    if not isinstance(selector, dict) or set(selector) - {"id", "name"}:
        return {"status": "invalid_input"}
    if not selector:
        return {"status": "missing_input"}
    if any(not isinstance(value, str) or not value.strip() for value in selector.values()):
        return {"status": "invalid_input"}
    if not complete or not isinstance(catalog, list):
        return {"status": "catalog_unavailable"}
    identities = set()
    for event in catalog:
        if not isinstance(event, dict):
            return {"status": "catalog_unavailable"}
        canonical_id = event.get("id")
        name = event.get("name")
        if (not isinstance(canonical_id, str) or not canonical_id.strip()
                or not isinstance(name, str) or not name.strip()
                or canonical_id in identities):
            return {"status": "catalog_unavailable"}
        identities.add(canonical_id)
    if "id" in selector:
        matches = [event for event in catalog if event["id"] == selector["id"]]
        if not matches:
            return {"status": "not_found"}
        selected = matches[0]
        if "name" in selector and selector["name"].strip().casefold() != selected["name"].strip().casefold():
            return {"status": "id_name_mismatch"}
    else:
        matches = [event for event in catalog
                   if event["name"].strip().casefold() == selector["name"].strip().casefold()]
        if not matches:
            return {"status": "not_found"}
        if len(matches) > 1:
            candidates = [{"id": event["id"], "name": event["name"]}
                          for event in sorted(matches, key=lambda event: event["id"])]
            return {"status": "ambiguous_name", "candidates": candidates}
        selected = matches[0]
    return {"status": "selected", "event": {"id": selected["id"], "name": selected["name"]}}
```

### Observable acceptance, tests and documentation

The following acceptance artifact specifies concrete inputs/outputs. The catalog
is synthetic and complete. Reversing its order must not change any result.

```json file=event-contract.json stage=acceptance
{
  "catalog": [
    {"id": "evt-39", "name": "Falls review"},
    {"id": "evt-14", "name": "Falls review"},
    {"id": "evt-82", "name": "Medication review"}
  ],
  "checks": [
    {"selector": {"name": " medication REVIEW "}, "result": {"status": "selected", "event": {"id": "evt-82", "name": "Medication review"}}},
    {"selector": {"name": "Falls review"}, "result": {"status": "ambiguous_name", "candidates": [{"id": "evt-14", "name": "Falls review"}, {"id": "evt-39", "name": "Falls review"}]}},
    {"selector": {"id": "evt-39", "name": "falls review"}, "result": {"status": "selected", "event": {"id": "evt-39", "name": "Falls review"}}},
    {"selector": {"id": "evt-39", "name": "Medication review"}, "result": {"status": "id_name_mismatch"}},
    {"selector": {}, "result": {"status": "missing_input"}},
    {"selector": {"id": null}, "result": {"status": "invalid_input"}},
    {"selector": {"name": "Missing event"}, "result": {"status": "not_found"}},
    {"selector": {"id": "EVT-39"}, "result": {"status": "not_found"}},
    {"selector": {"name": "Falls review"}, "complete": false, "result": {"status": "catalog_unavailable"}}
  ]
}
```

Required tests: all artifact rows, blank/invalid inputs, empty catalogs, malformed
and duplicate IDs, unchanged input records, order independence, and UI confirmation
disabled for every non-selected result. An integration test must show explicit
disambiguation passes the selected canonical ID to the existing submit API and
preserves its unauthorized/stale-event failures. Update selector/API documentation
with normalization, candidate shape, failure states and ID authority. A live UI
test and real submit integration are not proved by the reference algorithm alone.

**Exclusions:** event creation/renaming, evidence IDs/timestamps, global catalog
search, new authorization rules, schema changes, fuzzy search and automatic
submission. Completion is the bounded behavior plus required tests/docs, not a
new framework or cleanup of the existing submission implementation.

## Fictional PRD: atomic warehouse CSV import

### Prerequisites and blocking decisions

Confirmed **for this example**: the existing authenticated inventory endpoint has
a complete authorized SKU catalog and an atomic `commit_batch(records)` facade.
It returns a receipt on success; an exception guarantees rollback. SKUs are
application-issued canonical IDs, not product labels. The owner has approved the
1 MiB/500-record synchronous import limit and quantities from 1 through 9999.

If the real writer cannot guarantee rollback, the storage owner must supply an
atomic boundary before this import can ship. Do not silently permit partial
writes. Unknown tenant access or quantity rules remain owner blockers, not guessed
technical defaults. No such blocker remains in this worked handoff.

### Outcome, baseline and bounded increment

Operators import a small stock-delivery CSV once, receiving either one receipt for
all records or a precise failure with no committed rows. Baseline: authenticated
ID-based stock additions through the atomic facade already work. Increment: one
CSV validator at that existing endpoint; preserve authorization, write schema and
rollback behavior. Use synchronous standard-library parsing plus one commit, not
a queue, plugin system, new datastore or per-record write loop.

### Exact contract and preferred design

- Input: `bytes`, at most 1,048,576 bytes including BOM; UTF-8, optional initial
  BOM. Parse comma-separated CSV with standard quoted fields/doubled quotes and
  LF or CRLF records, strict quote parsing and the standard 131,072-character
  per-field parser ceiling (`invalid_csv` above it). The application must retain
  that parser ceiling. No delimiter sniffing or other encoding.
- Header is exactly `sku,quantity`, in that order, with no duplicate/extra fields.
  Require 1–500 data records. Blank records are invalid; a final line ending does
  not add a record. Row numbers are CSV record ordinals including the header,
  not physical line numbers inside quoted fields.
- Each row has exactly two fields. `sku` is an exact case-sensitive catalog ID:
  never generate, trim, case-fold or replace it with a product name. Empty/blank
  IDs fail. Missing/unknown catalog identity fails; an incomplete/unavailable or
  malformed/duplicate-SKU catalog cannot establish membership.
- `quantity` is ASCII decimal `[1-9][0-9]{0,3}` (1–9999); no whitespace, sign,
  decimal, leading zero or Unicode digit. Duplicate SKUs in one file fail rather
  than silently sum or pick a row. No upsert of unknown products.
- Validate the entire file before the one existing atomic write. Error precedence:
  input type/size, UTF-8/CSV grammar, header, record count, catalog availability,
  then first invalid record in file order (shape, ID, membership, duplicate,
  quantity). No truncation or partial success. Never execute a cell as a formula.
- `validate_import(payload, catalog, complete)` returns `ready` with ordered
  canonical `records: [{sku, quantity: integer}]`, or `invalid` with `error`
  from the design below and `record` only for row errors. `import_inventory`
  calls `commit_batch` exactly once only when ready and returns
  `{status: "imported", receipt_id, count}`. A rollback exception propagates
  through the existing error handler, with no retry or success receipt.

### Executable reference design

```python file=inventory_import.py stage=design
import csv
import io
import re


def validate_import(payload, catalog, complete=True):
    if not isinstance(payload, bytes):
        return {"status": "invalid", "error": "invalid_payload"}
    if len(payload) > 1_048_576:
        return {"status": "invalid", "error": "file_too_large"}
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {"status": "invalid", "error": "invalid_utf8"}
    try:
        rows = list(csv.reader(io.StringIO(text, newline=""), strict=True))
    except csv.Error:
        return {"status": "invalid", "error": "invalid_csv"}
    if not rows or rows[0] != ["sku", "quantity"]:
        return {"status": "invalid", "error": "invalid_header"}
    if len(rows) == 1:
        return {"status": "invalid", "error": "missing_rows"}
    if len(rows) - 1 > 500:
        return {"status": "invalid", "error": "too_many_records"}
    if not complete or not isinstance(catalog, list):
        return {"status": "invalid", "error": "catalog_unavailable"}
    identities = set()
    for product in catalog:
        if not isinstance(product, dict):
            return {"status": "invalid", "error": "catalog_unavailable"}
        sku = product.get("sku")
        if not isinstance(sku, str) or not sku.strip() or sku in identities:
            return {"status": "invalid", "error": "catalog_unavailable"}
        identities.add(sku)
    records = []
    imported_ids = set()
    for record_number, row in enumerate(rows[1:], start=2):
        error = None
        if len(row) != 2:
            error = "invalid_columns"
        elif not row[0].strip():
            error = "missing_sku"
        elif row[0] not in identities:
            error = "unknown_sku"
        elif row[0] in imported_ids:
            error = "duplicate_sku"
        elif re.fullmatch(r"[1-9][0-9]{0,3}", row[1]) is None:
            error = "invalid_quantity"
        if error:
            return {"status": "invalid", "error": error, "record": record_number}
        imported_ids.add(row[0])
        records.append({"sku": row[0], "quantity": int(row[1])})
    return {"status": "ready", "records": records}


def import_inventory(payload, catalog, commit_batch, complete=True):
    result = validate_import(payload, catalog, complete)
    if result["status"] != "ready":
        return result
    receipt_id = commit_batch(result["records"])
    return {"status": "imported", "receipt_id": receipt_id, "count": len(result["records"])}
```

### Acceptance, tests and documentation

Given catalog `[{sku: "stock-21"}, {sku: "stock-67"}]`, importing
`sku,quantity\nstock-21,2\nstock-67,4\n` calls the atomic facade once with those
two IDs and integer quantities in that order, then reports its receipt/count 2.
Given a valid first row and `stock-67,0` next, the result is
`{status: "invalid", error: "invalid_quantity", record: 3}` and the writer is
never called. A duplicate `stock-21` row produces `duplicate_sku` at record 3,
not an update. An unknown product name cannot replace a SKU.

Required behavioral tests: valid batches, BOM/CRLF/quoted IDs, first/last allowed
quantities and record count, each invalid input/error shape, duplicate/unknown
IDs, incomplete catalogs, late-row rejection with no write, unchanged catalog,
and write exception propagation without retry. Test the real facade's rollback
separately before release; a mock cannot prove database atomicity. Document exact
CSV schema, size/count limits, canonical SKU authority, error order/record numbering
and all-or-nothing behavior with one valid and one rejected sample file.

**Exclusions:** background jobs, new inventory identities, label lookup, spreadsheet
formula evaluation, partial import, cross-request retry/idempotency redesign,
evidence/timestamp generation, deployment and unrelated parser/API refactors.

## Verification boundary

Repository tests execute these design blocks and their acceptance data, including
failure/ambiguity behavior and no-write boundaries. They are illustrative contract
checks, not independent model outputs, live UI acceptance, warehouse transactions
or proof that the originating application currently has these interfaces.
