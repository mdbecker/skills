# Release checks

Release artifacts contain the selected skills, their complete resources, the
installer, attribution and source-bound qualification records. Project contracts
are mapped with `resources/project-profile.md`; examples define their own inputs.

## Content inspection

```sh
.venv/bin/python scripts/check_public_content.py --input working --with-export
.venv/bin/python scripts/check_public_content.py --input index --private-rules /path/to/rules.json
.venv/bin/python scripts/check_public_content.py --archive dist/skills-dev.zip --private-rules /path/to/rules.json
```

Working mode reads current tracked and nonignored new files. Index mode reads
stage-0 Git blobs and link targets without staging or modifying them. Inspect
working exports separately from index input. Archive inspection validates the
manifest and bounded entries before reading contents, without extraction.

External policy files contain named rules and literal values. Keep sensitive
configuration outside the candidate; use rule IDs and scoped locations in reports,
not matched values. Public examples and tests use invented inputs:

```json
{"rules":[{"id":"sample-rule","literal":"Sample Token"}]}
```

Raw and nested JSON text, paths and links are checked. Invalid paths, conflicted
index stages and uninspectable inputs block the selected check. A missing optional
policy is reported as not-run, not as comprehensive content acceptance.

## Approval and qualification

Content checks, semantic review, distribution rights, source-history review and
release approval are independent gates. Confirm the exact versioned inputs and
artifact identities. Exclude credentials, local configuration, planning notes,
caches and undeclared assets from release artifacts. Staging, commits, tags,
remotes and publication require their own explicit authority.

Stable and prerelease generation require content, policy, semantic, rights and
history approval. Prerelease labeling can disclose unperformed host/model checks;
it does not waive publication gates. The checker never infers publication-ready
status. Local fixture tests and installer placement are not host invocation,
model quality or domain validity.

## Verification records

Results identify actual commands, input hashes, outcomes and unperformed checks.
Keep evaluator-only criteria separate from raw actor inputs. A result applies only
to its recorded inputs; repeat affected verification when those inputs change.
Do not substitute invented observations, inferred approval or a test count for a
required independent review. Publication proceeds only after all applicable gates.
