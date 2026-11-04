# Validation baseline identities

Recorded before validation changes on November 4, 2026. The implementation checkout
started at `96528682f7f7fac47d45ab437070aa4364602652` with other agents' unstaged
and untracked work; the index had no staged changes. These unrelated edits are
not the validation patch and must not be reset, deleted or unstaged. Later
concurrent changes require their own attribution, not an unchanged-checkout claim.

## Documentation-driven comparator

For behavioral qualification the baseline is **documentation-driven**, not a
previous agent answer: identical frozen fixture repositories, requests, current
project instructions and command definitions, without the candidate skill.
The candidate arm additionally receives the exported validation guidance. Use the
same host/model/settings, tool availability, permission scope and suitable
environment for both arms. Freeze the materialized input identities at trial
creation; the harness must not disclose expected outcomes to executors.

The original short validation method is a versioned historical comparison input,
not evidence that a baseline agent executed anything. Recover the exact files
from the starting revision if inspecting the instruction delta:

| Source at starting revision | SHA-256 |
|---|---|
| `README.md` | `89dd09d920a36ae45ac9d5b64be6a77602feaf74f0348125f013693980d5fe3a` |
| `develop/SKILL.md` | `b9480009eb8fa5af1c79e922dbbf933c7a06e5034962b837c5f9a7f5be4b8403` |
| `develop/references/validate-repo.md` | `c9f221d29a79e0b39766e3d9b133492e3a7788a608fb16d6d69cbd6d841d3054` |
| `resources/profiles/template.md` | `5cc9bc31aff3d432d3dd4cdd90e08abdbdbe0ff1eeba68b07f2e984763447604` |

## Retained evaluator corpus

These pre-extension full-file hashes protect the existing cases/expected outcomes
from silent rewrites. The six substantive cases live in a separate frozen corpus;
adding them does not reinterpret prior expectations.

| Existing evaluation file | SHA-256 |
|---|---|
| `evaluations/fixtures.json` | `6b89095f05bba27ccc0138379ef64d99877d74eedc7089f47a92a96cbed567b0` |
| `evaluations/expected.json` | `69f3e2cb3a24a47bbdfc5abb905fd6cef28772c54de4f22a2e2c22634f38055e` |
| `evaluations/artifacts.json` | `d9619b9fcfd088df85631e2698b9bf578aa8ebfeb65c8e437d28bdeb70bea9c9` |

## Reference project context

The four supplied files were read locally at template revision
`52f1bfd61cbe1cc44b9c181123a9d584d28fbec1`. Their observed content hashes are below;
they are contextual authority for the reference profile, not command-execution
permission or evidence that the template's own tests/deployment were run. Raw
private project files are not redistributed in the fixture package.

| Supplied template file | SHA-256 |
|---|---|
| `AGENTS.md` | `908c7657166b0b5cf6f0f0767b14bffd204d30e4b12942e5a4ba19568601b233` |
| `.pre-commit-config.yaml` | `1027ddc415f95c78b131b4261ab7a0f471425d94da94396be9c08cff3f8f9cbb` |
| `noxfile.py` | `3593893994ba8a9409a2b0b77510a0ad0ee88ce39192871c6a0a73a310863914` |
| `docs/ARCHITECTURE.md` | `6687e3444e0b6469fea5ea076947fdf13ecb01b1a346615b42cf45e10a51edeb` |

## Evidence boundary

No matched model-mediated baseline/candidate run has been performed. Deterministic
baseline/patch command results in isolated fixture repositories prove fixture
behavior only. Tokens, cost and elapsed agent-run time remain unobserved separately;
no approved 1.5× tolerance or unchanged-performance claim exists.
