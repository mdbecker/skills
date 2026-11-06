# Explicit BDD

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Use for requests to implement specified behavior with failing tests first, or to
review Given/When/Then scenarios. Natural-language intent counts; an explicit
command is not required. Behavioral-test review is read-only. Ordinary testing
does not select this lifecycle, and a suggestion does not replace active Iterate.
When test-first is requested or required by current project policy, honor that
sequence rather than routing through Iterate's ordinary code-before-tests stage;
resolve any consequential conflict with an active lifecycle before editing.

Before authoring scenarios, check their quality:
- Cover one observable behavior per scenario with concrete examples.
- Derive expected results independently; do not copy production logic into the oracle.
- Keep scenarios understandable to product owners, testers and engineering
  stakeholders, and valid after behavior-preserving refactoring.
- Avoid tautologies and noncontractual call-count, ordering, formatting or
  internal-collaborator assertions. Contractual safety and side-effect checks remain valid.

1. Define observable acceptance outcomes, preserved behavior and relevant negative
   or security cases as concrete Given/When/Then scenarios in domain language.
2. Keep characterization tests. Define and run the complete agreed behavioral scenario set
   for the bounded increment before changing production. Run new behavioral tests
   against the unchanged baseline and inspect the failure:
   the intended assertion must fail for the specified missing behavior. Record
   the test, command, failing assertion and baseline used.
3. If a scenario already passes, investigate existing behavior, setup and whether
   the test reaches the real boundary. Retain valid coverage; do not weaken the
   implementation or assertion to manufacture red. An import, dependency or
   environment error is blocked execution, not behavioral red; repair an
   authorized prerequisite and rerun before proceeding.
4. Only after intended red, implement the lowest-complexity complete behavior;
   rerun to observe green, then check preserved behavior and relevant boundaries.
   Newly discovered behavior gets its own intended-red-before-production sequence;
   unrelated optional future scenarios are not prerequisites for this increment.

Assert outputs, persisted effects and stable architectural boundaries;
stub external dependencies rather than internal collaborators.
Interaction assertions are valid when that interaction itself is contractual.
Keep governance/static checks separate.

Return scenarios, focused authorized edits/docs, actual red/green results and
unperformed checks. Given/When/Then vocabulary inside Iterate does not constitute
test-first fidelity. For a complete canonical-identity/no-write implementation,
including an executable warehouse transfer and actual red/green procedure, read
[worked BDD](bdd-worked.md). The [public design ledger](resources/provenance.json) distinguishes
fictional examples from observed behavior. Map actual project fields locally.
