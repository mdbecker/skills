# Explicit BDD

Use for requests to implement specified behavior with failing tests first, or to
review Given/When/Then scenarios. Natural-language intent counts; an explicit
command is not required. Behavioral-test review is read-only. Ordinary testing
does not select this lifecycle, and a suggestion does not replace active Iterate.
When test-first is requested or required by current project policy, honor that
sequence rather than routing through Iterate's ordinary code-before-tests stage;
resolve any consequential conflict with an active lifecycle before editing.

1. Define observable acceptance outcomes, preserved behavior and relevant negative
   or security cases as concrete Given/When/Then scenarios in domain language.
2. Keep characterization tests. Write new behavioral tests before changing
   production. Run them against the unchanged baseline and inspect the failure:
   the intended assertion must fail for the specified missing behavior. Record
   the test, command, failing assertion and baseline used.
3. If a scenario already passes, investigate existing behavior, setup and whether
   the test reaches the real boundary. Retain valid coverage; do not weaken the
   implementation or assertion to manufacture red. An import, dependency or
   environment error is blocked execution, not behavioral red; repair an
   authorized prerequisite and rerun before proceeding.
4. Only after intended red, implement the lowest-complexity complete behavior;
   rerun to observe green, then check preserved behavior and relevant boundaries.

Assert outputs, persisted effects and stable architectural boundaries;
stub external dependencies rather than incidental internal collaborators.
Interaction assertions are valid when that interaction itself is contractual.
Keep governance/static checks separate.

Return scenarios, focused authorized edits/docs, actual red/green results and
unperformed checks. Given/When/Then vocabulary inside Iterate does not constitute
test-first fidelity. For a complete canonical-identity/no-write implementation,
including an executable warehouse transfer and actual red/green procedure, read
[worked BDD](bdd-worked.md). Source `bdd` is mapped in
[provenance](resources/provenance.json); source-project field names are not
universal defaults.
