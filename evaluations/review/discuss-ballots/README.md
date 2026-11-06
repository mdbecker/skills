# Discuss ballot integrity

This is the active corpus for Discuss voting trials. Keep only the current inputs
here; use Git history for superseded revisions. Update inputs, independent criteria
and their hashes deliberately. Do not recompute hashes merely to fit candidate
behavior or rewrite prior observed results to describe changed inputs. Each trial
must identify its actual source commit and corpus hashes.

`cases.json` contains raw requests/context/artifacts; `expected.json` contains
independent evaluator-only criteria. `freeze.json` pins both and `baseline.json`,
which identifies the pre-change Git source used for baseline comparisons rather
than copying old skill implementations. Cases include neutral actor context,
referenced policies, unlabeled tally records, and separate single-pass Discuss,
Code Debate and Smells Debate inputs. No fixture is an observed agent run.

## Trial setup

Use the existing evaluation protocol and separately approved host/model, artifact,
action, retention, spend/time/token scope. Supply actors only the selected request,
context and permitted raw artifacts, with the required installed instructions.
Keep case IDs, expected criteria, freeze identities and previous scoring out of
actor contexts. Match baseline/candidate tools, settings and evidence; inspect
actual calls, retained peer handles, packets, comparisons and final dispositions.
Do not score literal phrasing or treat a complete JSON shape as adequate reasoning.

Checkpoint reports, ballots, validation status and failures are explicitly
synthetic inputs. Establish and retain real peer contexts for any actual same-peer
follow-up exercise; map fixture labels without counting synthetic reports as votes.
Label checkpoint-only coverage separately from observed end-to-end initial
isolation and lifecycle behavior. Unsupported checkpoint access remains blocked,
not simulated completion. Tally records provide validation status only for the
classification exercise, not evidence of live deliberation or qualification.

For order/endorsement diagnostics, the trial setup reads `variants.json` and
materializes only one selected packet as `decision-packet.json` for each independent
matched run. Do not expose the variant list, other packets or earlier results to
actors. Keep the request/context and substantive evidence fixed; retain all outputs
and report sensitivity rather than rerunning until agreement. These diagnostic
judgments are not additional substantive votes or ballot-recovery calls.

The route-code and route-smells cases include explicit commands, complete inert
Python source and a behavioral contract. They exercise their existing Debate
initial assessments and disagreement-only ballot selection; the single-pass case
separately checks that Discuss does not spawn peers without explicit Debate.

## Checks and limits

Run `.venv/bin/python -m unittest tests.test_discuss_distribution -v`. The integrity
check requires hashes for cases, independent criteria and baseline before checking
digests. Its negative regression omits each required entry and mutates that file in
a temporary copy. Package tests exercise actual Review-only installation and
evaluator exclusion on both host layouts. None of these tests claims agent
judgment quality or uses Markdown substring assertions.

Behavioral/model/host acceptance remains `not_run`. Baseline/candidate observations,
if separately approved, must record actual follow-ups, comparative adequacy,
factual support, minority retention, mode selection and available telemetry.
Existing qualification records are not promoted by updating this corpus.
