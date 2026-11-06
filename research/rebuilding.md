# Transactional rebuilding and honest verification

Load whenever assembling/rebuilding a report or claiming verification. Map the
existing editable sources, saved evidence, derived assets, generated outputs,
dependencies, allowed commands and check targets with
[the profile](report-profile.md). Missing dependencies block the affected
operation; do not invent a pipeline, run notebooks or silently omit sections.

## Snapshot, stage, check, commit

1. **Coordinate and snapshot.** Honor the project's active-work conventions.
   Before editing, retain versions/full hashes of relevant evidence, schemas,
   templates, helpers, diagram/configuration/manifests, canonical presentation
   sources, declared dependencies and the current output. Watch existence and
   path-set changes as well as content. A quiet interval or timestamp alone is
   not a concurrency guarantee. Preserve unrelated agents' edits.
2. **Establish the intended input checkpoint.** After authorized source changes,
   capture the expected post-edit input hashes for this build. Retain the earlier
   checkpoint for evidence comparison; intentional edits are not concurrency
   failures. Check protected evidence and exact correction scope before building.
3. **Stage without touching the destination.** Use the existing builder's mapped
   staging/output mechanism. Generate to a unique temporary destination on the
   final destination's filesystem; do not truncate/delete the prior report first.
   If the existing command writes only in place and cannot be safely staged under
   its established configuration, block replacement rather than creating a new
   production reporting platform. Snapshot/retain the destination's original hash
   or explicit absence for first creation.
4. **Check staged artifacts.** Run mapped source/asset identity, ledger, chart,
   archive, disclosure, diagram, structural and required browser/visual checks
   against the staged output. A checker hard-coded to the old final report cannot
   validate the new stage. Record its actual target and artifact hash. Failures,
   missing required checks, absent sections and incomplete output block commit.
5. **Recheck concurrent changes.** Immediately before commit, compare all relevant
   inputs/path sets against the intended input checkpoint and the current
   destination against its original checkpoint. Include changes during checks,
   deletion/creation and a newly created report during first assembly. Abort on
   change; preserve the concurrent author's output, not a stale backup. If safe
   commit exclusion is required, use the mapped cooperative lock/check-and-replace
   protocol: a hash check followed by rename alone does not eliminate a writer
   racing between those operations.
6. **Atomic local replacement.** Only after required checks pass, replace the
   destination atomically using the mapped same-filesystem mechanism. Multi-file
   bundles need a mapped atomic directory/version-switch strategy; separate
   per-file renames are not a bundle transaction. Atomic local replacement is not
   sending, publication or deployment. Record the committed output hash.
7. **Failure cleanup.** On builder/check/concurrency failure, leave the existing
   report intact and remove only this run's staging material under the mapped
   policy. For first creation preserve inputs and do not expose incomplete output
   as a finished report. Keep failure diagnostics safely; never clean up other
   agents' work or roll their destination back to your old version.

Post-commit checks, when needed, refer to the committed hash and remain separate
from pre-commit gates. If a later check fails, report it honestly; use only an
authorized mapped recovery strategy, never an automatic destructive rollback.

Map whether the builder and every required checker can target the same staged
artifact before replacement. Record staged and final paths/hashes separately.
A builder that stages internally then replaces `build-report.html`, followed by
a checker hard-coded to that final file, does not satisfy staged acceptance.
Block replacement unless an existing permitted isolated build/check arrangement
supports it; otherwise name separately authorized builder/checker adaptation as
the prerequisite. Do not invent isolation, change outside projects, weaken checks
or create a reporting platform to bypass this boundary.

## Check matrix

Adapt the applicability and required-for-commit column to the target; do not
invent check commands. Browser/visual prerequisites unavailable means blocked or
not-run, not a pass. For a task whose acceptance requires those checks, withhold
the verified-complete claim and commit as the mapped policy requires.

| Check | Required evidence of completion |
|---|---|
| Protected evidence | Semantic before/staged-after ledger comparison, with only supported authorized deltas; all affected surfaces checked. |
| Charts | Exact series/cell values and states, labels, units, denominator populations, cohort switches, legends and encoding; actual visual inspection where applicable. |
| Disclosure | Dual thresholds, accounting/reorder, approved output fields, complement/indirect-release review including hidden/embedded data. |
| Archives | Extraction scope/completeness, component provenance, independent full expected hash for exact reconstruction. |
| Diagrams/assets | Source/configuration/asset identity, decisions/loops/optional edges, static safety, unique IDs and resolved references. |
| Controls/links/anchors | Actual keyboard controls, expand/collapse/search/reset/copy as present; resolved internal links and no duplicate anchors. |
| Runtime/offline | Mapped browser execution, console-error capture and request log; no unexpected external network requests under the profile. |
| Narrow/desktop/print | Screenshots or observed views, readable content, overflow behavior, print contents and restored screen behavior. |
| Transaction | Prior-output checkpoint, stage target, failed-build preservation, concurrent-change detection and successful atomic replacement only when gated. |

Static `inspect_html` assistance cannot prove control behavior, console cleanliness,
network inactivity or visual legibility. Keep an actual browser request log and
visual inspection record when these are required. A previously checked report or
reference project's audit is not verification of this build.

## Outcomes and limits

Use a separate record for each check:

```yaml
check_id: <mapped check>
target_sha256: <full staged or committed artifact digest>
status: <completed | failed | blocked | not-run>
result: <pass | fail | null>
command: <actual invocation or null for manual inspection>
evidence: <captured result/log/screenshot or null>
reason: <failure, missing prerequisite or intentionally omitted scope>
```

- `completed` / `pass`: actually executed/inspected the recorded target and met
  the criterion. Exit success alone cannot establish unrelated criteria.
- `failed` / `fail`: an actual check ran and failed; preserve diagnostics.
- `blocked` / `null`: a required prerequisite/access/dependency was unavailable.
- `not-run` / `null`: not attempted; state why and whether it was required.

Successful assembly is not proof of visual inspection, independent review,
scientific validity, historical reproducibility, universal performance parity,
or successful agent execution. Documentation, packaging and mutation tests are
not evidence that a reference/transfer task was actually performed.

After profile mapping, `transactional_build` and `inspect_html` in
`research/scripts/report_checks.py` may assist the mapped operation. Inspect their
actual API, staging assumptions and concurrency coverage first; they are helpers
after mapping, not a replacement pipeline or an assumed CLI.
