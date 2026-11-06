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
`--agents <COUNT>` selects at least two peers, default three. The main agent maps
disagreements, verifies claims, collects private ballots from the same peers, and
writes the report. It votes only on valid ties; factual dispositions follow evidence,
and tradeoff votes cannot replace missing user criteria or required owner decisions.
