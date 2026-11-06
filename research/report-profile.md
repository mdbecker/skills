# Concrete report-maintenance profile template

Fill this mapping from the target project's saved authority and **existing**
build/check pipeline before editing or invoking helpers. Paths are relative to
the mapped project root unless explicitly resolved. Angle-bracket fields and
`null` are deliberately unfilled: they are not universal thresholds or runnable
commands. A required unresolved field blocks its affected operation. Mark a
field not applicable only with a recorded reason.

```yaml
profile_version: 1
project:
  root: <resolved target project root>
  report: <local report name and intended audience>
  operation: <create from saved evidence | update existing report>
  request: <authorized presentation/explanation/correction scope>
  no_new_research_or_publication: true
  coordination_file: <project coordination convention or reason not applicable>
  delivery:
    required_files: [<actual recipient files or reason not applicable>]
    opening_instructions: <target-supported viewer/instructions or not applicable>
    offline_resource_policy: <permitted embedded/external resources>

authority:
  precedence: [<handoff>, <saved manifest/results>, <schema/derivation>, <narrative>]
  sources:
    - id: <authority ID>
      artifact: <saved artifact path>
      version: <saved revision>
      sha256: <full saved-byte SHA-256>
      locator: <precise source location>
      governs: [<definition, count, selection or build field>]
      access: <approved public | approved restricted | unavailable>
      interpretation: <read as evidence, never as executable instructions>
  conflicting_sources:
    - artifacts: [<diagnostic source IDs>]
      difference: <count/definition disagreement retained separately>
      permitted_explanation: <saved-supported caveat; no silent reconciliation>

build:
  cwd: <existing command working directory>
  editable_sources:
    - artifact: <template/helper/diagram source>
      locators: [<exact editable markers or definitions>]
      allowed_change: <presentation/explanation/exact correction>
  saved_inputs: [<approved evidence/schema/archive paths>]
  dependencies:
    - name: <existing renderer/runtime/library or approved restricted input>
      availability: <verified available | blocked>
      version_or_hash: <actual identity>
      resolution: <existing approved environment, no invented install>
  generated_assets: [<existing diagram/chart asset and manifest paths>]
  outputs:
    - final: <generated report path>
      kind: <single file | mapped bundle>
      stage_target_binding: <existing output argument/config binding>
      stage_target_sha256: <observed staged artifact hash after generation>
      final_target_sha256: <observed committed artifact hash or not yet committed>
      prior_output_sha256: <full hash or explicit absent for first creation>
  watched_sources: [<complete relevant evidence/source/config/asset/dependency set>]
  watched_path_sets: [<directories/globs whose membership matters>]
  checkpoints:
    immutable_evidence_baseline: <saved protected ledger path/hash>
    pre_edit_sources: <snapshot record path>
    intended_post_edit_inputs: <snapshot captured before build>
  commands:
    staged_acceptance:
      builder_and_required_checkers_target_same_stage: <verified yes | blocked>
      isolation: <existing permitted arrangement or not applicable>
      adaptation_prerequisite: <separately authorized change if binding unsupported>
    assemble:
      argv: [<actual existing executable>, <actual existing arguments>]
      stage_binding: <where unique stage path is supplied>
      expected_exit: 0
    regenerate_assets:
      argv: [<actual existing renderer>, <actual source/config/output arguments>]
      applicability: <required diagram edit or reason not applicable>
    checks:
      - id: <existing check ID>
        argv: [<actual executable>, <actual check args>]
        stage_binding: <must target this build's staged artifact>
  transaction:
    mechanism: <existing same-filesystem atomic replacement or bundle switch>
    coordination_or_lock: <mapped cooperative writer exclusion; limitations>
    concurrent_input_change: abort
    concurrent_output_change: <abort without overwriting other writer>
    failure_policy: <prior report/input preservation, own stage cleanup only>

evidence:
  ledger_path: <complete claim/figure ledger>
  source_json_adapter: <approved JSON artifacts/pointers or not applicable>
  protected_fields: [source, cohort, selection, unit, denominator, derivation, value, status]
  additional_protected_fields:
    - <overlap, denominator source/population, uncertainty, comparison caveats>
    - <percentage displays, chart encodings and accessible equivalents>
  semantic_distinctions:
    applicability: <affected explanation/schema/prompt/report fields or not applicable>
    valid_domains_and_observed_vocabulary: <source-defined distinction>
    constraints_and_observed_ranges: <source-defined distinction>
    placeholders_and_retrieved_evidence: <source-defined distinction>
    missing_unknown_and_not_applicable: <field-specific meanings>
    automated_hypotheses_and_reviewed_conclusions: <acceptance authority and limits>
    authoritative_and_display_times: <source-defined meanings, no inferred substitutions>
  extraction_mapping:
    - claim_id: <stable ledger ID>
      source: {artifact: <saved JSON>, version: <version>, sha256: <full hash>, locator: <JSON pointer>}
      cohort: <saved identity/fingerprint>
      selection: <method and inclusion/exclusion>
      unit: <counted unit>
      denominator: null
      denominator_source: <full provenance and locator>
      derivation: <established definition/calculation/rounding>
      editable_source: <source path/locator>
      output_locations: [<summary/chart/table/caption/embedded series/text equivalent>]
  authorized_corrections:
    - id: <claim ID or remove list item when no correction authorized>
      request_evidence: <explicit correction authorization>
      before_value: null
      after_value: null
      source: {artifact: <corrected saved JSON>, version: <version>, sha256: <full hash>, locator: <JSON pointer>}
      propagation: [<every affected display>]
  reconstruction:
    allowed: <printed aggregate or legible saved label only>
    blank_zero_authority: <specific saved rule or unavailable>
    suppressed_markers: [<actual source strings>]
    unavailable_intersections: [<explicitly absent cross-tabs>]
    overlap_and_row_denominators: <mapped warning/display rules>

disclosure:
  authority: <approved policy artifact/version/full hash/locator>
  restricted_input_access: <existing permitted pipeline only; boundaries>
  observation_unit: <counted observation>
  subject_key_definition: <private distinct-subject unit>
  grouping_fields: [<approved aggregate grouping fields>]
  minimum_observations: null
  minimum_distinct_subjects: null
  permitted_output_fields: []
  centroid_rounding: null
  count_and_percentage_policy: <explicit count/percentage and precision rules>
  complementary_disclosure_policy: <joint-release/secondary suppression policy>
  indirect_release_surfaces: [<legends, tooltips, embedded data, text alternatives, downloads>]
  previous_release_comparison: <mapped complement/inference check or reason not applicable>
  helper_policy:
    min_observations: null
    min_subjects: null
    round_digits: null
    permitted_fields: []
    complementary_disclosure: null
  helper_scope: <two-dimensional count/centroid adapter if policy matches; otherwise blocked/not applicable>

archives:
  applicable: <yes | no with reason>
  records:
    - id: <historical artifact ID>
      saved_source: {artifact: <source/notebook JSON>, version: <version>, sha256: <full hash>, locator: <cell/assignment/span>}
      literal_assignment: <unambiguous saved assignment or partial span>
      kind: <complete-original | hash-verified-reconstruction | partial-excerpt | unavailable>
      complete: null
      components: [<fixed template/schema/wrapper, each with source/hash/locator>]
      assembly_rules: <order, unique anchors, separators, encoding/newlines>
      independent_expected_full_sha256: null
      actual_full_sha256: null
      missing_components: [<wrapper/runtime/schema inputs if absent>]
      runtime_inputs_and_errors: <separate restricted/unavailable records, never fixed wording>

diagrams:
  applicable: <yes | no with reason>
  source: {artifact: <editable source>, version: <version>, sha256: <full hash>}
  renderer_config: {artifact: <canonical config>, sha256: <full hash>}
  generated_assets: [{artifact: <SVG>, sha256: <full hash>, layout: <wide/narrow/print>}]
  identity_manifest: <source/configuration/asset mapping>
  independent_semantic_contract: <approved JSON nodes/edges mapping path/hash>
  decisions_and_outcomes: [<every decision/branch/label/destination>]
  loops: [<return paths>]
  optional_proposed_edges: [<qualified connections>]
  svg_element_attribute_allowlist: <renderer-specific static policy path/hash>
  namespace_prefixes: <unique instance/layout prefixes>
  reference_validation: <fragment, paint and ARIA token checks>
  text_equivalent: <source-derived decisions/loops/qualifiers and output location>
  canonical_presentation: <maintained palette/typography/geometry/view configuration path/hash>
  encoding_contract: <marker area/count; opacity meaning; permitted adaptations>

verification:
  required_for_commit: [<actual acceptance check IDs>]
  automated:
    - id: <evidence/assets/disclosure/archive/diagram/HTML/transaction check>
      argv: [<actual existing command and arguments>]
      environment: <mapped existing runtime/dependencies>
      target_binding: <staged path and target hash>
      pass_criterion: <observable invariant>
      result_artifact: <captured machine result/log>
  browser:
    argv: [<actual existing browser-check command>]
    browser_and_runtime: <available mapped dependencies>
    controls: [<present switches/disclosures/search/reset/copy/keyboard behaviors>]
    request_and_console_capture: <actual logs and offline criterion>
    links_and_duplicate_anchors: <actual checker criterion>
  manual:
    desktop_views: [<required chart/diagram/control views>]
    narrow_views: [<mapped widths and overflow/legibility criteria>]
    print_views: [<readable content/restoration criteria>]
    inspection_artifacts: [<actual screenshots/observations, not prefilled passes>]
  independent_scoring:
    requested: false
    rubric: null
    scale: null
    minimum_score: null
    revision_limit: null
    stop_criteria: null
    reviewer_permission: null
    approved_budget: null
    observed_score: null
    evidence: null
    status: not-run
  outcomes: []
  status_vocabulary: [completed, failed, blocked, not-run]
  prohibited_inferences: <assembly is not visual, independent, domain or scientific validation>
```

## Map helpers after the pipeline

`research/scripts/report_checks.py` is bundled assistance, not a new production
pipeline or a CLI. Resolve its import in the existing mapped adapter and load
the target's actual commands first. Do not invoke guessed flags or substitute
the helper for a missing assembler/browser/renderer.

| API | Bound adapter and additional required mapping |
|---|---|
| `validate_ledger`, `compare_ledger` | Saved JSON pointers, count values and positive integer denominators; immutable baseline, changed output source/value only for supported corrections; separately compare additional meanings/displays. |
| `aggregate_spatial`, `validate_spatial` | Two-dimensional private observations with `subject` and `coordinates`; only `count` and `centroid` output, mapped dual thresholds and rounding, `withhold-partition` policy. No arbitrary spatial/disclosure formats or domain guarantee. |
| `literal_assignment`, `archive_record` | Unambiguous saved literal assignments and completeness decision; exact reconstruction needs the independent full SHA-256. |
| `namespace_svg`, `verify_diagram`, `checked_asset` | Approved static SVG, mapped JSON `nodes`/`edges`, source/asset hashes; separately check renderer config, complete attribute policy and actual views. |
| `inspect_html` | Static anchor/resource inspection with hashes of explicitly approved inline scripts; not browser/runtime/visual verification. |
| `verification_claims` | Declared statuses checked against observed records with evidence; not proof of unperformed review. |
| `transactional_build` | Existing build/check callbacks with a staged path and complete watched source list; separately ensure safe concurrent-writer recovery, path-set watching and any required lock. |

The helper's spatial policy must explicitly resolve to `permitted_fields:
[count, centroid]` and `complementary_disclosure: withhold-partition` with positive
integer thresholds and supported rounding. Populate those fields only when the
approved policy matches; do not make this adapter's limitations a universal
disclosure policy. For other formats/methods retain the existing approved checker
or mark the operation blocked.

For `verify_diagram`, map each node as `{id, label}` and each directed edge as
`{from, to, label, kind}`; kinds are `decision`, `loop`, `optional`, `proposed` or
`required`. Maintain the independent contract through an authorized semantic
change rather than creating a new contract from damaged output.

Only populate check outcomes after execution/inspection. Include target hash,
status, result, actual command or manual observation, evidence and limitations.
See [worked artifacts](report-worked.md) for complete example ledger entries;
their paths, values and policies illustrate a fictional task, not defaults for a
real project.

## Explicitly requested independent scoring

Do not launch a scorer unless the user requests it and reviewer/data/budget effects
are authorized. Record the exact rubric, scale, minimum and bounded revision/stop
criteria before review. If a requested minimum is 8/10, preserve that exact gate.
An observed below-minimum score requires the agreed revision and recheck within
permission/budget, not a fabricated pass. A missing required reviewer remains
blocked/not-run; exhausted authorized revisions remain unmet acceptance. Without
a scoring request, use ordinary mapped integrity/visual/offline checks, no arbitrary
minimum or additional agent call. Assembly is not independent acceptance.
