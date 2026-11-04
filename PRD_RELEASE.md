# PRD: Self-Contained Skill Release and Project Installation

## Goal

From another project, a user downloads one release zip and says **“install the
skills in this zip file.”** Its root README gives the agent enough information to
install complete project-local skills without this conversation, source checkout,
global installation or automatic workflow execution. This extends the approved
export architecture in PRD.md, not a new skill family or generic agent framework.

## Release artifact

Generate `skills-<version>.zip` and a companion SHA-256 file from the exact tagged
commit. Include root README, manifest, auditable standard-library `install.py`,
LICENSE/NOTICE, and complete ordinary `skills/<name>/` folders from the explicit
inventory. Bundle canonical references/helpers into each parent's and legacy
entrypoint's resource closure. Exclude state, scratch, environments, restricted
data, credentials, repository history and evaluation answers.

The manifest identifies schema/package/version/commit, source hashes, every
payload file/hash, inventory, host locations and qualification status. Do not
claim planned skills, unverified host invocation or missing quality gates passed.
Internal hashes are integrity checks, not proof of publisher authenticity.

## Installation contract

The agent reads the archive's README/manifest/installer as data before execution,
identifies the target project and host, and retains platform approvals. Use existing
Python 3.11+; no automatic downloads. The installer accepts explicit archive/project,
host, optional selected skills, dry-run, trusted checksum and authorized upgrade.
Codex targets `.agents/skills`; Claude Code targets `.claude/skills`.

Validate complete inventories/hashes and bounded regular-file paths before target
writes; reject traversal, symlinks, duplicates, case collisions and undeclared
entries. Install full folders with a receipt, not links to a temporary extraction.
Identical reinstalls are unchanged; conflicting unmanaged or locally modified
folders abort. Upgrade only unchanged previously managed files, preserving unrelated
work. Stage replacements, lock concurrent installs and roll back failed writes.
No global settings/hooks, workflow execution, Git mutations or publication.

README-driven installation must work with one request when project/host are known
and no conflict exists; necessary platform approvals are not bypassed. Report
actual installation and host discovery/invocation separately. Missing runtime or
permissions produce a precise blocker and validated manual-copy instructions.

## GitHub automation

Add a version-tag workflow and a manual existing-tag dispatch. Checkout the exact
trusted commit, run canonical checks and bundle-install tests, export deterministically,
then attach zip/checksum to a draft release before publication. Limit write-token
permissions to release work; do not publish from pull-request code or silently
overwrite an existing asset. A failed required check stops publication.

Stable publication requires PRD.md's reviewed quality/host gates. Explicitly
labeled prereleases may carry blocked/not-run qualification records without
claiming full acceptance. Implementing this workflow does not authorize an actual
tag, push, release publication or global installation in this task.

## Acceptance

- Rebuilding the same version/source/status yields identical archive bytes.
- A fresh temporary project installs selected parents/aliases and runs the
  packaged helper after removal of the source/extraction context.
- Dry-run, identical reinstall, unchanged managed upgrade, local-edit conflict,
  unrelated files and rollback/concurrent-lock cases have observed outcomes.
- Corrupt hashes, malicious paths, duplicate entries and symlink escapes fail
  before replacement. No files are written outside the selected host directory.
- Existing manifest/metadata checks and new bundle tests pass; real host/model
  checks remain honestly qualified rather than simulated by packaging tests.
- CI failure or unmet stable gates cannot publish a stable release; prerelease
  assets and release notes disclose remaining acceptance limits.
