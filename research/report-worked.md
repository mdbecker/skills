# Worked report-maintenance artifacts

This is a self-contained, fictional nonclinical example of the methods, not a
new reporting platform, runnable dependency bundle, or claim of agent execution.
The existing target pipeline must first be mapped using
[the profile template](report-profile.md). Evaluation fixtures may use different
bytes/paths; read their actual manifests instead of assuming these sample hashes.

## Saved evidence specification

For this example alone, `evidence/cohorts.json` version `reliability-v1` consists
of the following single UTF-8 line **plus one LF newline**:

```json
{"A":{"identity":"cohort-A-random-v1","selection":"random service-day sample","unit":"service-days","numerator":24,"denominator":120},"B":{"identity":"cohort-B-incident-v1","selection":"incident-enriched service-day sample","unit":"service-days","numerator":16,"denominator":40}}
```

Its full SHA-256 is
`e193b79648c8e84581c29c6cfec2217662f2d55e16d98c21f836268e14ae2a01`.
The numerator means service-days with the saved qualifying event, denominator
means eligible service-days in that cohort. This is a supplied aggregate
definition; no record-level data or new computation is required. Cohort overlap
and saved uncertainty intervals are unavailable.

## Complete baseline ledger

These two count records conform to the bounded JSON-pointer helper. Additional
fields document the fuller evidence contract. They are immutable baseline
records, not an output ledger rewritten after a correction.

```yaml
ledger_version: 1
entries:
  - id: cohort-a
    source:
      artifact: evidence/cohorts.json
      version: reliability-v1
      sha256: e193b79648c8e84581c29c6cfec2217662f2d55e16d98c21f836268e14ae2a01
      locator: /A/numerator
      authority: approved saved aggregate, not a later narrative paraphrase
    cohort: cohort-A-random-v1
    selection: random service-day sample
    unit: service-days
    overlap: unavailable; not assumed disjoint, independent or matched with B
    denominator: 120
    denominator_population: eligible service-days in cohort A
    denominator_source:
      artifact: evidence/cohorts.json
      version: reliability-v1
      sha256: e193b79648c8e84581c29c6cfec2217662f2d55e16d98c21f836268e14ae2a01
      locator: /A/denominator
    derivation: saved qualifying-event service-days / eligible service-days; percent = 100 * count / denominator, one decimal for this example
    derivation_source: saved aggregate definition stated above; numerator and denominator JSON pointers
    value: 24
    status: exact
    uncertainty: saved interval unavailable; no new interval inferred
    comparison_limit: selection differs from B; difference does not establish improvement
    editable_source: templates/report.html; cohort-a panel, summary and text alternative
    output_location: ["report.html#cohort-a", "cohort-a series", "cohort-a summary", "cohort-a accessible table"]
    permitted_change:
      kind: presentation
      scope: spacing, ordering and labels without changing protected values or meanings
      authorization: improve chart layout without changing results
    verification:
      status: not-run
      result: null
      command: null
      artifact: null
      reason: worked documentation; target assembly/comparison/visual checks not executed
  - id: cohort-b
    source:
      artifact: evidence/cohorts.json
      version: reliability-v1
      sha256: e193b79648c8e84581c29c6cfec2217662f2d55e16d98c21f836268e14ae2a01
      locator: /B/numerator
      authority: approved saved aggregate, not a later narrative paraphrase
    cohort: cohort-B-incident-v1
    selection: incident-enriched service-day sample
    unit: service-days
    overlap: unavailable; not assumed disjoint, independent or matched with A
    denominator: 40
    denominator_population: eligible service-days in cohort B
    denominator_source:
      artifact: evidence/cohorts.json
      version: reliability-v1
      sha256: e193b79648c8e84581c29c6cfec2217662f2d55e16d98c21f836268e14ae2a01
      locator: /B/denominator
    derivation: saved qualifying-event service-days / eligible service-days; percent = 100 * count / denominator, one decimal for this example
    derivation_source: saved aggregate definition stated above; numerator and denominator JSON pointers
    value: 16
    status: exact
    uncertainty: saved interval unavailable; no new interval inferred
    comparison_limit: incident-enriched cohort is not a random-population prevalence estimate or evidence of improvement
    editable_source: templates/report.html; cohort-b panel, summary and text alternative
    output_location: ["report.html#cohort-b", "cohort-b series", "cohort-b summary", "cohort-b accessible table"]
    permitted_change:
      kind: presentation
      scope: spacing, ordering and labels without changing protected values or meanings
      authorization: improve chart layout without changing results
    verification:
      status: not-run
      result: null
      command: null
      artifact: null
      reason: worked documentation; target assembly/comparison/visual checks not executed
```

A layout candidate must preserve `24/120 (20.0%)` and `16/40 (40.0%)`, their
count/denominator pairs and meanings in visible charts and embedded data.
Expected rejection examples include `24→25`,
changing B's selection to random, losing a cohort, or describing `40%` versus
`20%` as improvement. `compare_ledger` checks its protected field set; mapped
checks additionally compare derived displays, denominator provenance, caveats and
accessible equivalents. A reordered pair of records is not a changed cohort.

## Explicitly supported correction

Suppose the user explicitly authorizes correcting **only** A's numerator using
`evidence/correction.json` version `reliability-v2`. Its bytes are the same single
line above with A's `"numerator":24` replaced by `"numerator":26`, plus LF. The
full SHA-256 is
`804e52700679e693248b7c91c504370a8a0e3da1b892175274be866d6c50ef80`.
Do not overwrite the original saved file or baseline ledger.

After resolving `report_checks` through the mapped existing adapter, use its
actual API with loaded baseline/staged records and this saved correction:

```python
from copy import deepcopy
from report_checks import compare_ledger

staged_entries = deepcopy(baseline_entries)
correction_source = {
    "artifact": "evidence/correction.json",
    "version": "reliability-v2",
    "sha256": "804e52700679e693248b7c91c504370a8a0e3da1b892175274be866d6c50ef80",
    "locator": "/A/numerator",
    "authority": "explicitly authorized saved corrected aggregate",
}
for entry in staged_entries:
    if entry["id"] == "cohort-a":
        entry["value"] = 26
        entry["source"] = correction_source
approved_corrections = [{
    "id": "cohort-a", "before_value": 24, "after_value": 26,
    "source": correction_source,
}]
compare_ledger(baseline_entries, staged_entries, mapped_project_root,
               corrections=approved_corrections)
expected_displays = {"cohort-a": "26/120 (21.7%)", "cohort-b": "16/40 (40.0%)"}
```

These calls require the exact saved sample files and mapped loaded records; they
are not a command to create a new pipeline. Record the authorization separately
and propagate `26/120 (21.7%)` to every A display. B remains `16/40 (40.0%)`,
with its original evidence source. Denominator/selection/unit/definition/status
do not change. The corrected source/hash change is allowed only on A's output
record; changing every output record's hash to the newest file is unauthorized.

## Suppression, blanks, missing intersections and conflicts

For this example, `evidence/cells.json` version `cells-v1` has these exact UTF-8
bytes plus LF, with full SHA-256
`cf7116c15274e283f5d4c0c870698aabcd096bfbd8fc209cf9dc96c59569d462`:

```json
{"cells":{"total":20,"disclosed":15,"remainder":"<11","intersection":null,"ambiguous_blank":null,"documented_zero":0},"definitions":{"current":"event_flag == true","saved_diagnostic":"event_flag != false"},"groups":{"overlap":"unavailable","denominators":{"A":120,"B":40}}}
```

Each additional record inherits that artifact/version/hash, the example's
service-day unit, its precisely sourced denominator and the same template/check
bindings; identify each cell with its own locator and output location:

| ID / source locator | Value / status | Denominator, editable/output binding and permitted decision |
|---|---|---|
| `partition-total` / `/cells/total` | `20` / exact internal saved total | 20 service-days in the saved partition; template/output partition panel; joint release with `15` and `<11` must be withheld under this example's complement policy. |
| `partition-disclosed` / `/cells/disclosed` | `15` / exact | Same 20 denominator; partition panel; preserve only policy-approved presentation, not a published derived remainder. |
| `partition-suppressed` / `/cells/remainder` | `"<11"` / suppressed | Same 20 denominator; partition panel/tooltip/text; remain nonnumeric, never publish `5` or numeric geometry. |
| `unavailable-intersection` / `/cells/intersection` | `null` / unavailable | Eligible intersection denominator unavailable; limitation text only; never invent an intersection from marginals. Do not force a fake denominator into the count helper. |
| `blank-cell` / `/cells/ambiguous_blank` | `null` / unavailable | Eligible source row not specified; limitation text; no conversion to zero without saved authority. |
| `documented-zero` / `/cells/documented_zero` | `0` / exact | Source explicitly supplies zero, not an unlabeled blank; mapped 20-day row; zero display permitted if disclosure policy allows. |
| `definition-comparison` / `/definitions` | Both literal definitions / disputed comparison | Definitions are not count records; explanatory caption preserves `event_flag == true` versus `event_flag != false` without silent reconciliation. |
| `overlap-caveat` / `/groups/overlap` | `unavailable` overlap / unavailable | Row denominators remain A=120 and B=40; caption/controls/text equivalent state unknown overlap and prohibit summing a partition. |

Their verification is `not-run`, `result: null` in this worked artifact. Actual
task ledgers must record the observed outcome, exact editable/output locators and
full denominator provenance. Keep non-count definition/unknown-denominator
records in the full ledger and mapped checker, not fabricated helper-compatible
numeric claims. Values come from these saved aggregates, never bar-height
estimates; no hidden intersection or suppressed value is reconstructed.

## Private aggregation and partial archive

For a **fictional policy only**, an 11-observation/11-distinct-subject gate
rejects 20 observations from two subjects. Two children of 11 observations from
11 distinct subjects each may split; a child failing either gate prevents the
split even if its sibling passes. All approved observations must be accounted
once; reordering input must preserve the canonical partition/output. Do not
assume distinct subjects across leaves or publish their identifiers.

In the existing mapped adapter, the bounded spatial calls are:

```python
from report_checks import aggregate_spatial, validate_spatial

policy = mapped_profile["disclosure"]["helper_policy"]
groups = aggregate_spatial(approved_private_observations, policy)
validate_spatial(approved_private_observations, groups, policy)
```

The filled policy must have actual `min_observations`, `min_subjects`, supported
`round_digits`, `permitted_fields: [count, centroid]` and
`complementary_disclosure: withhold-partition`. The private observation shape is
`{subject: <private stable string>, coordinates: [<x>, <y>]}`; output is only
count and rounded centroid. Joint-release legends/percentages/tooltips still need
the mapped checks. Marker area may encode count; mixed-group opacity must not
imply an individual severity/attribute.

`evidence/archive.py` consists of the following UTF-8 line plus LF, full source
hash `36661f2eac767b4d15ec84dabac856c3c30419cc93dce9593cb10ea754b8faef`:

```python
INSERTION = "Retain unresolved items for review."
```

Its original wrapper/runtime context is missing. `literal_assignment(source,
"INSERTION")` can recover the exact string; `archive_record(text,
"partial-excerpt", complete=False)` is the appropriate record. The source-file
hash is not the extracted string's hash and proves neither the missing wrapper
nor a complete runtime prompt. An exact reconstruction needs all components and
an independently saved matching full artifact SHA-256; no later wrapper or
hash-prefix match can substitute.

## Editable decision diagram and failed build

The example's editable `diagrams/workflow.mmd` has these UTF-8 bytes plus LF;
full source SHA-256 is
`528c6e9ce9adcbe9f32d72ed57cdee7bb17bc031be37ae4351827bbf83a7dace`:

```text
flowchart TD
  START["Saved evidence"] --> CHECK{"Evidence usable?"}
  CHECK -->|yes| BUILD["Stage report"]
  CHECK -->|no or unknown| REVIEW["Review limitation"]
  REVIEW --> CHECK
  BUILD -.->|proposed independent review| OPTIONAL["Independent review"]
```

Map a JSON semantic contract with nodes `{id, label}` and edges
`{from, to, label, kind}` for `verify_diagram`. Preserve both decision outcomes,
the review loop and the proposed connection in source, generated graphic and
text equivalent. Regenerate through the mapped renderer, verify source/config/
asset identity, and namespace every embedded SVG instance and its references.
No scripts/external resources or false claim that independent review occurred.

Expected transaction outcomes, not claimed execution results:

| Scenario | Required result |
|---|---|
| Existing assembler returns failure after writing a stage | Report prior bytes/hash unchanged; only own stage cleaned; assembly `failed`, dependent checks `not-run` or `blocked`. |
| Check fails or a required check cannot run | No replacement; failed/blocked criterion separately recorded, not recast as assembly success. |
| Another writer changes a watched source/output | Abort and preserve their changes; never restore your stale snapshot over their report. |
| Required staged checks pass with stable inputs/output | Mapped atomic local replacement; record committed hash and only actual completed checks. |

The helper `transactional_build(root, sources, output, build, checks=())` takes
callbacks that invoke existing mapped commands against its supplied stage.
Verify its actual recovery/concurrency behavior against the profile before use;
it is not a substitute for writer coordination or a complete path-set watch.
`inspect_html` is static only, and `verification_claims` compares declared
statuses to observed records: neither creates browser/visual/reviewer evidence.
Do not claim those checks completed when they were blocked or not run.
