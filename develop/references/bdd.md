# Explicit BDD

Select this lifecycle explicitly or from current project policy. Behavioral-test
review is read-only. Never activate test-first merely because ordinary feature
work mentions testing, or change an active Iterate phase without a decision.

Identify acceptance outcomes, preserved behavior and relevant negative/security
cases. Describe focused concrete Given/When/Then in domain language. Write new
behavioral tests before production changes and observe the intended red outcome;
an already-passing scenario needs investigation, not manufactured failure. An
environment/import failure is not the required behavioral failure.

Implement the minimum complete solution, preserve characterization coverage, and
observe green. Assert outputs, persisted effects and stable boundary behavior;
stub external dependencies rather than incidental internal collaborators.
Interaction assertions are valid when that interaction itself is contractual.
Keep governance/static checks separate.

Return scenarios, focused authorized edits/docs, actual red/green results and
unperformed checks. Given/When/Then vocabulary inside Iterate does not constitute
test-first fidelity. See the BDD cases in [examples](../resources/examples.md) and
source `bdd` in [provenance](../resources/provenance.json).
