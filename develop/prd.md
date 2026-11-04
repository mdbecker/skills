# Implementation specification

Use for requests to write or revise a concise, decisive implementation handoff,
including natural-language requests without a mode command. Drafting does not
implement the proposed feature.

Establish user outcome, current baseline, proposed increment and compatibility.
Put prerequisites and consequential blocking owner decisions first. Select one
preferred complete design using correctness, simplicity, maintainability, project
fit and likely usage; expose genuine business/access/domain unknowns rather than
leaving supported technical choices to the implementer. The target is the
cleanest, clearest, lowest-complexity solution that fully addresses the outcome,
not merely the smallest patch. State the chosen design and why it fits the known
constraints; do not leave an unranked menu of architectures.

Specify contracts, identities, time semantics, ambiguous/missing inputs, failure
behavior, exclusions, acceptance scenarios, docs and validation. Remove repetition,
placeholders and references to unavailable conversation context. Historical
cleanroom assumptions are not permission to remove current compatibility. Name
the authoritative identity source, preserve canonical IDs across display-name
lookup, and make duplicate names an explicit ambiguity rather than selecting the
first match. Define limits, transaction/side-effect boundaries and recovery where
they affect observable behavior. A handoff must stand alone for a new developer.

Resolve technical choices from supplied evidence. Separately label genuine owner
decisions (for example access scope or allowed data loss), the decision owner and
the affected blocked work; never fabricate approval or bury a blocker in a later
implementation step. A complete worked example may state confirmed prerequisites,
but those synthetic confirmations are not authority in a live project.

Return the concise developer handoff and bounded unknowns. Drafting does not
execute the specification, initialize a feature manifest, commit, or replace
Iterate's real-options architecture/user-approval checkpoint. Read
[worked PRDs](prd-worked.md) when a complete name/ID-ambiguity handoff or bounded
CSV-import specification would clarify the contract. They include executable
reference algorithms and acceptance data, not deployed implementations or model
evaluation results. Sources are mapped in
[provenance](resources/provenance.json).
