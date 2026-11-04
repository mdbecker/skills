# Disclosure-safe aggregate presentation

Load when an approved pipeline processes restricted observations or when counts,
centroids, legends, tooltips or embedded data can disclose small groups. Use the
project's authorized disclosure policy, not a threshold borrowed from a clinical
example. Missing policy blocks the affected aggregate release.

## Required policy mapping

Record the authority, unit, minimum observations **and** minimum distinct
subjects, subject-key definition, grouping fields, allowed output fields,
coordinate precision/rounding, count/percentage rules and complementary-disclosure
policy in [the profile](report-profile.md). A subject may contribute multiple
observations; passing one threshold never implies passing the other. Subject
keys may be used internally only with approved access and must not enter output.

A fictional configuration requiring 11 observations and 11 distinct subjects
rejects 20 observations from two subjects. Eleven is example configuration, not a
universal privacy standard. Neither aggregation nor a threshold check certifies
formal de-identification.

## Spatial aggregation gates

1. Validate the approved input manifest and full checksum. Verify finite geometry,
   subject identity availability, cohort scope and permitted grouping fields.
   Invalid observations are a failed/blocked aggregate, not silently dropped
   records. Do not fetch missing restricted material to fill gaps.
2. Establish a deterministic internal order and partition rule. Bind coordinate
   dimensions, split axis/tie rules and centroid calculation to the mapped method;
   a presentation edit must not invent a different scientific derivation.
3. Require the parent group to satisfy both thresholds before release. A split is
   permitted only if **both children** independently satisfy both thresholds.
   Check actual distinct subject sets, not summed per-record counts. If either
   child fails, retain the approved parent aggregate; if no safe parent exists,
   withhold the aggregate with an explicit reason.
4. Assert that child observation sets are disjoint and their union is the parent.
   At completion each approved observation belongs to exactly one leaf: the leaf
   union equals the input set, pairwise intersections are empty, and the sum of
   counts equals input observations. Track internal membership privately.
   Subjects can span leaves; subject counts therefore must not be summed as if
   leaves held disjoint subject populations.
5. Repeat with permuted input order. Compare canonically sorted membership and
   published aggregates, using stable summation and mapped rounding so tied
   partitions/floating-point order cannot change publication. Do not publish an
   order-dependent boundary or suppress different groups after a shuffle.
6. Project output through the explicit allowlist. A typical approved shape is
   a group label, approved count and rounded group centroid; use it only if the
   profile authorizes each field. No individual coordinates, record identifiers,
   subject keys, record text or private membership arrays survive into HTML,
   SVG, JSON, downloads, captions or accessibility metadata.

Retention as a parent is not permission to publish every marginal/category count
within that parent. Group counts, subject counts and centroid precision each
need their own approval; a private accounting assertion is not a public field.

## Complements and indirect disclosure

Apply the policy to the **joint release**, not each visible chart in isolation.
Totals, sibling counts, marginals, percentages, overlapping filters, legends,
tooltips, accessible tables, downloads, source comments and embedded arrays can
reveal withheld cells together. Hiding a control does not remove its payload.

- Keep suppressed values nonnumeric. Do not place a recoverable numeric value in
  CSS widths, SVG geometry, `data-*`, a tooltip or an accessible label.
- Evaluate whether an approved total and visible siblings reveal a suppressed
  complement. Withhold/aggregate additional cells, a total or a percentage only
  as the mapped policy permits; record the chosen withholding and retain exact
  evidence in its approved internal location. Never publish a derived remainder
  merely because subtraction is possible.
- A dominance percentage together with a subgroup total can reveal a small
  secondary category. Rounded percentages are not automatically safe. Check
  inferability at the published precision, including ranges and previous releases.
- Check restricted identifiers/text by output-field allowlisting as well as
  forbidden-field scans. Absence of a few known identifier strings does not prove
  absence of record-level disclosure.
- Preserve caveats when a group combines categories. If marker **area** encodes
  count, preserve that mapping and legend. Mixed-group opacity must not imply
  individual severity or another unsupported individual attribute; use the
  mapped aggregate encoding, including uniform opacity where specified.

## Verification boundary

After mapping, the disclosure aggregation APIs in
`research/scripts/report_checks.py` may help enforce dual thresholds, accounting,
deterministic reorder and output allowlists. Verify their actual coverage and add
the target's complementary-disclosure checks to the mapped existing checker.
An aggregation helper alone does not inspect every indirect-release surface or
establish a privacy guarantee. Record the check input/output artifact and actual
completed, failed, blocked or not-run outcome using [rebuilding](rebuilding.md).
