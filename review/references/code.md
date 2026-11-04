# Code review

Establish declared target/snapshot, comparison if applicable, requirements,
instructions, protected contracts, relevant callers/tests/docs, prior findings and
compatibility. Current-source review without a base is valid but cannot claim a
defect was introduced by an unknown diff. Never silently widen to a structural audit.

Review intent, architecture/responsibility, correct maintainable implementation,
then material polish. Inspect actual usage to substantiate dead code, harmful
duplication, leaky abstraction, needless generalization/specialization, conditional
complexity, scattered changes, mixed ownership, fragile tests and stale docs/names.
Do not spend findings on properly applied automation unless it is missing or wrong.

Missing a dependency in the reviewer environment is not automatically a code defect;
a missing declared production dependency may be. Cleanroom cleanup applies only
when established; unknown compatibility is not removal permission.

Each finding: stable ID, verified location, evidence/consequence, one preferred
complete remedy/rationale, introduced/worsened/relevant-pre-existing status,
compatibility assumptions and fix-now/defer recommendation. Urgency is Must fix
before merging / Should fix now / Optional recommended now / Optional can defer;
feedback type TODO / Question / Follow-up / Nit. Keep urgency separate from impact
severity and structural S0–S3.

Recheck revised findings against current evidence: resolve verified fixes, update
open items, withdraw stale/unsupported claims with reasons and merge duplicates
without dropping IDs. No actionable findings is valid. Return requested format,
coverage and actual/not-run checks; no edits or posting are implied.
