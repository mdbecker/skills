# Technical discussion

For inputs, context/defaults, named controls and effects, use
[the shared usage reference](resources/usage.md).

Establish the decision, current baseline, authoritative constraints, relevant raw
artifacts, alternatives and consequential unknowns. Compare genuine options using
correctness, simplicity, ownership, compatibility, likely use and operational cost.
Prefer one supported decision; expose genuine unresolved business/access/domain
tradeoffs rather than force consensus or a menu of unsupported fixes.

Separate verified source claims, conditional hypotheses and preferences. Inspect
counterevidence and consequential omissions; disagreement is not a defect. Honor
requested output format and explain evidence/limits. Discussion is read-only and
does not authorize implementation, model calls or publication by itself.

Single-pass is default. Explicit `--engine debate` uses the bundled flat voting
protocol and model/host preflight without changing scope or permissions. Debate-only
`--agents <COUNT>` selects at least two peers, default three. The main agent keeps
the original peer handles/history and a decision ledger linking each consequential
choice to original claims and explicit initial positions, including `not_addressed`.
Every eligible choice receives an actual follow-up ballot from every original peer,
including unanimous recommendations and choices raised by only one peer. Skip
ballots only when no eligible choices remain, with ledger exclusion reasons.

Use the Debate method's canonical packet and ballot instructions: neutral atomic
alternatives, shared evidence/criteria, all-option comparisons, and the decisive
tradeoff against the strongest rival. Validate substance before tallying; a token
counterargument is not comparative justification. Report actual follow-ups,
per-peer votes, validation failures, changed judgments, dissent, and unresolved
choices. A material packet defect requires abstention/unresolved disposition;
substantive revision requires a separately authorized new run, not ballot repair.

The main agent votes only on valid ties. Factual dispositions follow evidence;
tradeoff votes cannot replace missing user criteria or required owner decisions.
The ledger, packet, ballot template, recovery and tally rules are owned by the
[flat voting protocol](debate.md); this summary does not define another procedure.
