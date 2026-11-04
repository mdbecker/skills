"""Independent frozen outcomes for the bounded synthetic report adapter, not agent routing."""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / "evaluations/research-report"
EXPECTED = json.loads((DIRECTORY / "expected.json").read_text())
CASES = {case["id"]: case for case in json.loads((DIRECTORY / "cases.json").read_text())["cases"]}
FREEZE = json.loads((DIRECTORY / "freeze.json").read_text())


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    previous = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


FIXTURES = load_module(DIRECTORY / "fixtures.py", "frozen_research_fixtures")
CHECKS = load_module(ROOT / "research/scripts/report_checks.py", "candidate_report_checks")


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = FIXTURES.create_fixture(Path(self.temporary.name) / "project")
        self.before = json.loads((self.root / "ledger.json").read_text())
        self.checker = load_module(self.root / "scripts/check_report.py", "existing_fixture_checker")

    def rejected(self, case, action, error=None):
        self.assertTrue(EXPECTED["cases"][case].startswith("reject"))
        with self.assertRaises(error or CHECKS.ReportCheckError):
            action()

    def mutated_entry(self, identity, **updates):
        after = deepcopy(self.before)
        next(entry for entry in after if entry["id"] == identity).update(updates)
        return after

    def parse_report(self, content=None):
        parser = self.checker.RenderedEvidence()
        parser.feed(content if content is not None else (self.root / "report.html").read_text())
        parser.close()
        return parser

    def assert_baseline(self, ledger, corrected=False):
        actual = {entry["id"]: entry for entry in ledger}
        self.assertEqual(set(actual), set(EXPECTED["baseline"]))
        for identity, expected in EXPECTED["baseline"].items():
            with self.subTest(identity=identity):
                values = dict(expected)
                if corrected and identity == "cohort-a":
                    values["value"] = EXPECTED["correction"]["after_value"]
                self.assertEqual({field: actual[identity][field] for field in values}, values)

    def assert_public(self, corrected=False):
        parsed = self.parse_report()
        self.assertEqual(set(parsed.rows), set(EXPECTED["baseline"]))
        for identity, expected in EXPECTED["baseline"].items():
            projected = dict(expected)
            projected.update(EXPECTED["public_projection"].get(identity, {}))
            if corrected and identity == "cohort-a":
                projected["value"] = EXPECTED["correction"]["after_value"]
            value = projected["value"]
            rendered = "Unavailable" if value is None else json.dumps(value, sort_keys=True) if isinstance(value, dict) else str(value)
            self.assertEqual(parsed.rows[identity], [identity, rendered, str(projected["denominator"]), projected["status"]])
        self.assertEqual(parsed.bars, {"A": EXPECTED["chart"]["corrected_A" if corrected else "A"], "B": EXPECTED["chart"]["B"]})


class FrozenCorpusTests(unittest.TestCase):
    def test_corpus_hashes_and_expected_case_identities_are_frozen(self):
        self.assertEqual(set(FREEZE["corpus_sha256"]), {
            "evaluations/research-report/fixtures.py", "evaluations/research-report/cases.json",
            "evaluations/research-report/expected.json"})
        for relative, digest in FREEZE["corpus_sha256"].items():
            self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)
        self.assertEqual(set(CASES), set(EXPECTED["cases"]))
        self.assertTrue(EXPECTED["evaluator_only"])
        for case in CASES.values():
            self.assertNotIn("expected", case)
            for relative in case["artifacts"]:
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn("..", Path(relative).parts)
                self.assertNotIn("expected.json", relative)

    def test_hash_api_matches_independent_standard_digest(self):
        self.assertTrue(issubclass(CHECKS.ReportCheckError, ValueError))
        self.assertEqual(CHECKS.sha256(b"abc"), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")

    def test_activation_cases_are_requests_not_claimed_model_route_results(self):
        self.assertEqual(EXPECTED["cases"]["layout"], "applicable")
        self.assertEqual(EXPECTED["cases"]["correction"], "applicable-scoped")
        self.assertEqual(EXPECTED["cases"]["experiment"], "outside-scope")
        self.assertEqual(EXPECTED["cases"]["new-pipeline"], "outside-scope")
        self.assertEqual(EXPECTED["cases"]["missing-dependency"], "blocked")
        entry = (ROOT / "research/SKILL.md").read_text()
        frontmatter = entry.split("---", 2)[1]
        self.assertIn("name: research", frontmatter)
        self.assertIn("description:", frontmatter)
        self.assertIn("saved", frontmatter)
        self.assertIn("pipeline", entry)
        self.assertIn("notebook", entry.lower())
        self.assertIn("publ", entry.lower())
        self.assertIn("not model routing", EXPECTED["qualification"])


class ReportTaskTests(FixtureCase):
    def test_reference_and_transfer_artifacts_match_frozen_values_and_public_projection(self):
        for profile in EXPECTED["profiles"]:
            with self.subTest(profile=profile), tempfile.TemporaryDirectory() as temporary:
                self.root = FIXTURES.create_fixture(Path(temporary) / "project", profile)
                self.checker = load_module(self.root / "scripts/check_report.py", "profile_checker")
                result = FIXTURES.run_task(self.root)
                self.assertEqual(result["status"], "completed")
                self.assertEqual(result["profile"], profile)
                self.assertEqual(result["presentation"], EXPECTED["presentation"])
                self.assertEqual(result["archive"], EXPECTED["archive"])
                self.assert_baseline(result["ledger"])
                self.assert_baseline(json.loads((self.root / "ledger.after.json").read_text()))
                self.assert_public()
                self.assertEqual(result["checks"][0]["rows"], 13)
                self.assertEqual(result["checks"][0]["bars"], 2)
                for name in ("visual-inspection", "keyboard-browser", "narrow-print-browser", "independent-agent"):
                    self.assertEqual(result["verification"][name], {"status": "not-run", "evidence": None})
                CHECKS.verification_claims({name: record["status"] for name, record in result["verification"].items()}, result["verification"])

    def test_supported_correction_changes_only_value_source_and_public_bar(self):
        result = FIXTURES.run_task(self.root, correction=True)
        self.assert_baseline(result["ledger"], corrected=True)
        self.assert_public(corrected=True)
        old = {entry["id"]: entry for entry in self.before}
        for entry in result["ledger"]:
            protected = set(entry) - {"verification"}
            if entry["id"] == "cohort-a":
                protected -= {"value", "source"}
            self.assertEqual({field: entry[field] for field in protected}, {field: old[entry["id"]][field] for field in protected})
        self.assert_baseline(json.loads((self.root / "ledger.json").read_text()))

    def test_failed_fixture_assembly_preserves_report_and_prior_ledger(self):
        FIXTURES.run_task(self.root)
        previous = (self.root / "report.html").read_bytes()
        ledger = (self.root / "ledger.after.json").read_bytes()
        with self.assertRaisesRegex(RuntimeError, "synthetic assembler failure"):
            FIXTURES.run_task(self.root, correction=True, fail=True)
        self.assertEqual((self.root / "report.html").read_bytes(), previous)
        self.assertEqual((self.root / "ledger.after.json").read_bytes(), ledger)
        self.assertEqual(list(self.root.glob(".report-stage-*")), [])

    def test_mapped_existing_cli_commands_really_assemble_check_correct_and_fail(self):
        mapping = json.loads((self.root / "build.json").read_text())
        previous = (self.root / "report.html").read_bytes()
        for corrected in (False, True):
            for name in ("assembly_argv", "check_argv"):
                arguments = [sys.executable] + [value.replace("{staged}", ".cli-stage.html") for value in mapping[name][1:]]
                if corrected:
                    arguments.append("--correction")
                completed = subprocess.run(arguments, cwd=self.root, capture_output=True, text=True, check=True)
                self.assertEqual(json.loads(completed.stdout)["status"], "completed")
            self.assertEqual((self.root / "report.html").read_bytes(), previous)
        failed = subprocess.run([sys.executable, mapping["assembler"], "--output", ".cli-stage.html", "--fail"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("synthetic assembler failure", failed.stderr)
        self.assertEqual((self.root / "report.html").read_bytes(), previous)
        refused = subprocess.run([sys.executable, mapping["assembler"], "--output", "report.html"], cwd=self.root, capture_output=True, text=True)
        self.assertNotEqual(refused.returncode, 0)
        self.assertEqual((self.root / "report.html").read_bytes(), previous)

    def test_missing_existing_dependency_blocks_without_omitting_sections(self):
        previous = (self.root / "report.html").read_bytes()
        (self.root / "scripts/check_report.py").unlink()
        with self.assertRaises((CHECKS.ReportCheckError, ValueError, FileNotFoundError)):
            FIXTURES.run_task(self.root)
        self.assertEqual((self.root / "report.html").read_bytes(), previous)

    def test_rendered_count_denominator_selection_and_graphical_mutations_are_rejected(self):
        original = (self.root / "report.html").read_text()
        mutations = [
            ("unauthorized-count", '<td class="value">24</td>', '<td class="value">25</td>'),
            ("cohort-meaning", '<td class="denominator">120</td>', '<td class="denominator">40</td>'),
            ("bar-width", 'style="width:20%"', 'style="width:30%"'),
            ("bar-percent", '24/120 (20%)', '24/120 (30%)'),
            ("bar-label", 'Cohort B — incident-enriched', 'Cohort B — random'),
            ("missing-intersection", '<td class="value">Unavailable</td>', '<td class="value">4</td>'),
        ]
        for case, before, after in mutations:
            with self.subTest(case=case):
                self.assertIn(before, original)
                target = self.root / "mutated.html"
                target.write_text(original.replace(before, after, 1))
                self.rejected(case, lambda: self.checker.check(self.root, target), ValueError)

    def test_suppressed_percentages_bars_tooltips_and_embedded_disclosure_are_rejected(self):
        original = (self.root / "report.html").read_text()
        cell = '<td class="value">&lt;11</td>'
        for replacement in ('<td class="value">5 (25%)</td>', '<td class="value"><span style="width:25%">&lt;11</span></td>', '<td class="value" title="5">&lt;11</td>'):
            with self.subTest(replacement=replacement):
                target = self.root / "mutated.html"
                target.write_text(original.replace(cell, replacement))
                self.rejected("suppressed-subtraction", lambda: self.checker.check(self.root, target), ValueError)
        for insertion in ('<p class="legend">20 minus 15 leaves 5</p>', '<span title="15">Withheld</span>', '<script type="application/json">{"disclosed":15}</script>'):
            target = self.root / "mutated.html"
            target.write_text(original.replace("</body>", insertion + "</body>"))
            self.rejected("complementary-disclosure", lambda: self.checker.check(self.root, target), ValueError)

    def test_complementary_projection_withholds_one_more_cell_without_mutating_private_evidence(self):
        self.assert_baseline(self.before)
        self.assert_public()
        original = (self.root / "report.html").read_text()
        target = self.root / "mutated.html"
        target.write_text(original.replace("Withheld (complementary disclosure)", "15"))
        self.rejected("complementary-cell", lambda: self.checker.check(self.root, target), ValueError)
        self.assertEqual(next(entry for entry in self.before if entry["id"] == "partition-disclosed")["value"], 15)


class EvidenceLedgerTests(FixtureCase):
    def test_saved_baseline_and_reordering_preserve_exact_ledger_values(self):
        self.assert_baseline(self.before)
        CHECKS.compare_ledger(self.before, list(reversed(deepcopy(self.before))), self.root)

    def test_unauthorized_value_changes_and_missing_or_duplicate_claims_fail(self):
        for after in (self.mutated_entry("cohort-a", value=25), self.before[:-1], self.before + [self.before[0]]):
            self.rejected("unauthorized-count", lambda: CHECKS.compare_ledger(self.before, after, self.root))

    def test_all_cohort_and_quantitative_meaning_fields_are_protected(self):
        for field, value in {"cohort": "A+B", "selection": "random", "unit": "findings", "denominator": 120,
                             "derivation": "new saved interpretation"}.items():
            with self.subTest(field=field):
                after = self.mutated_entry("cohort-b", **{field: value})
                self.rejected("cohort-meaning", lambda: CHECKS.compare_ledger(self.before, after, self.root))

    def test_suppressed_unavailable_blank_and_disputed_values_cannot_be_fabricated(self):
        for case, identity, value in [("suppressed-subtraction", "partition-suppressed", 5),
                                      ("missing-intersection", "unavailable-intersection", 4),
                                      ("blank-to-zero", "blank-cell", 0),
                                      ("diagnostic-reconciliation", "diagnostic-first", {"definition": "reconciled events", "count": 19})]:
            with self.subTest(identity=identity):
                self.rejected(case, lambda: CHECKS.compare_ledger(self.before, self.mutated_entry(identity, value=value), self.root))

    def test_saved_zero_is_numeric_zero_not_blank_boolean_or_string(self):
        for value in (None, False, "0"):
            with self.subTest(value=value):
                artifact = self.root / "evidence/not-a-zero.json"
                artifact.write_text(json.dumps({"value": value}))
                modified = deepcopy(self.before)
                record = next(entry for entry in modified if entry["id"] == "established-zero")
                record["source"] = {"artifact": "evidence/not-a-zero.json", "version": "synthetic-v1", "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "locator": "/value"}
                with self.assertRaises(CHECKS.ReportCheckError):
                    CHECKS.compare_ledger(modified, deepcopy(modified), self.root)

    def test_labeled_reconstruction_rejects_bar_height_subtraction_or_marginals(self):
        for derivation in ("estimated bar height", "total minus disclosed subtraction", "marginal totals intersection"):
            invalid = self.mutated_entry("labeled-aggregate", derivation=derivation)
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.compare_ledger(invalid, deepcopy(invalid), self.root)

    def test_correction_requires_matching_explicit_saved_authorization(self):
        corrections = json.loads((self.root / "corrections.json").read_text())
        after = self.mutated_entry("cohort-a", value=25, source=corrections[0]["source"])
        CHECKS.compare_ledger(self.before, after, self.root, corrections)
        for changes in ({"before_value": 23}, {"after_value": 26}, {"id": "missing"}):
            invalid = deepcopy(corrections)
            invalid[0].update(changes)
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.compare_ledger(self.before, after, self.root, invalid)
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.compare_ledger(self.before, after, self.root, corrections * 2)
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.compare_ledger(self.before, self.mutated_entry("cohort-a", value=25, source=corrections[0]["source"], selection="enriched"), self.root, corrections)

    def test_correction_cannot_promote_suppressed_cell_to_exact(self):
        evidence = self.root / "evidence/forbidden-correction.json"
        evidence.write_text('{"count":5}')
        source = {"artifact": "evidence/forbidden-correction.json", "version": "v1", "sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(), "locator": "/count"}
        correction = {"id": "partition-suppressed", "before_value": "<11", "after_value": 5, "source": source}
        self.rejected("suppressed-subtraction", lambda: CHECKS.compare_ledger(self.before, self.mutated_entry("partition-suppressed", value=5, status="exact", source=source), self.root, [correction]))

    def test_source_full_hash_version_locator_and_path_are_required(self):
        for field, value in (("sha256", "0" * 64), ("sha256", "abc"), ("version", ""),
                             ("locator", "/missing"), ("locator", "A/numerator"),
                             ("artifact", "../outside.json"), ("artifact", str(self.root / "evidence/cohorts.json"))):
            invalid = deepcopy(self.before)
            invalid[0]["source"][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.compare_ledger(invalid, deepcopy(invalid), self.root)
        invalid = deepcopy(self.before)
        del invalid[0]["denominator"]
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.compare_ledger(invalid, invalid, self.root)

    def test_escaped_json_pointer_and_array_locator_resolve_saved_values(self):
        source = self.root / "evidence/escaped.json"
        source.write_text('{"a/b":{"~key":[24]}}')
        changed = deepcopy(self.before)
        changed[0]["source"] = {"artifact": "evidence/escaped.json", "version": "v1", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "locator": "/a~1b/~0key/0"}
        CHECKS.compare_ledger(changed, deepcopy(changed), self.root)

    def test_nested_disputed_count_and_uncertainty_boolean_coercion_are_rejected(self):
        source = self.root / "evidence/small-dispute.json"
        source.write_text('{"saved":{"definition":"small saved events","count":1}}')
        original = deepcopy(self.before)
        record = next(entry for entry in original if entry["id"] == "diagnostic-first")
        record.update(value={"definition": "small saved events", "count": 1}, source={"artifact": "evidence/small-dispute.json", "version": "v1", "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "locator": "/saved"})
        changed = deepcopy(original)
        next(entry for entry in changed if entry["id"] == "diagnostic-first")["value"]["count"] = True
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.compare_ledger(original, changed, self.root)
        original = deepcopy(self.before)
        original[0]["uncertainty"] = [0, 1]
        changed = deepcopy(original)
        changed[0]["uncertainty"] = [False, True]
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.compare_ledger(original, changed, self.root)


class SpatialTests(unittest.TestCase):
    def setUp(self):
        self.policy = deepcopy(EXPECTED["spatial"]["policy"])

    def test_coincident_observations_accounted_once_and_centroid_rounded(self):
        observations = [{"subject": "subject-" + str(index), "coordinates": [1.23456, 2.34567]} for index in range(24)]
        actual = CHECKS.aggregate_spatial(observations, self.policy)
        self.assertEqual(actual, EXPECTED["spatial"]["coincident"])
        CHECKS.validate_spatial(observations, actual, self.policy)
        self.assertEqual(sum(group["count"] for group in actual), len(observations))
        self.assertEqual(CHECKS.aggregate_spatial(list(reversed(observations)), self.policy), actual)

    def test_distinct_subject_threshold_rejects_twenty_observations_from_two_subjects(self):
        observations = [{"subject": "subject-" + str(index % 2), "coordinates": [index, 0]} for index in range(20)]
        self.assertEqual(CHECKS.aggregate_spatial(observations, self.policy), EXPECTED["spatial"]["two_subjects"])

    def test_separated_children_meet_both_thresholds_and_input_order_is_irrelevant(self):
        observations = [{"subject": "left-" + str(index), "coordinates": [-10 + index / 10, index / 10]} for index in range(12)]
        observations += [{"subject": "right-" + str(index), "coordinates": [10 + index / 10, 2 + index / 10]} for index in range(12)]
        actual = CHECKS.aggregate_spatial(observations, self.policy)
        self.assertEqual(actual, EXPECTED["spatial"]["separated"])
        self.assertEqual(CHECKS.aggregate_spatial(observations[::2] + observations[1::2], self.policy), actual)
        CHECKS.validate_spatial(observations, deepcopy(EXPECTED["spatial"]["separated"]), self.policy)

    def test_unpublishable_child_is_not_subtracted_or_dropped(self):
        observations = [{"subject": "left-" + str(index), "coordinates": [0, 0]} for index in range(12)]
        observations += [{"subject": "right-repeat", "coordinates": [10, 0]} for unused in range(10)]
        self.assertEqual(CHECKS.aggregate_spatial(observations, self.policy), [{"count": 22, "centroid": [4.55, 0.0]}])

    def test_thresholds_are_configurable_not_universal_eleven(self):
        policy = dict(self.policy, min_observations=2, min_subjects=2, round_digits=1)
        observations = [{"subject": "one", "coordinates": [1.26, 2.26]}, {"subject": "two", "coordinates": [1.26, 2.26]}]
        self.assertEqual(CHECKS.aggregate_spatial(observations, policy), [{"count": 2, "centroid": [1.3, 2.3]}])

    def test_policy_and_coordinate_input_fail_closed(self):
        observations = [{"subject": "one", "coordinates": [0, 0]}]
        for field, value in (("min_observations", 0), ("min_subjects", True), ("round_digits", -1),
                             ("permitted_fields", ["count", "centroid", "subject"]), ("complementary_disclosure", "ignore")):
            with self.subTest(field=field), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.aggregate_spatial(observations, dict(self.policy, **{field: value}))
        for invalid in ({"subject": "one", "coordinates": [float("nan"), 0]}, {"subject": "one", "coordinates": [True, 0]},
                        {"subject": 1, "coordinates": [0, 0]}, {"coordinates": [0, 0]}, {"subject": "one", "coordinates": [0]}):
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.aggregate_spatial([invalid], self.policy)

    def test_output_forbids_private_fields_unrounded_centroids_and_false_accounting(self):
        observations = [{"subject": "subject-" + str(index), "coordinates": [1.23456, 2.34567]} for index in range(24)]
        for groups in ([{"count": 24, "centroid": [1.23, 2.35], "subject": "private"}],
                       [{"count": 24, "centroid": [1.23456, 2.34567]}],
                       [{"count": 23, "centroid": [1.23, 2.35]}],
                       [{"count": 24.0, "centroid": [1.23, 2.35]}]):
            with self.subTest(groups=groups), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.validate_spatial(observations, groups, self.policy)


class ArchiveTests(unittest.TestCase):
    def test_literal_assignments_do_not_execute_other_source(self):
        source = 'EXCERPT: str = "Keep saved labels."\nraise RuntimeError("must never execute")\n'
        self.assertEqual(CHECKS.literal_assignment(source, "EXCERPT"), "Keep saved labels.")
        for source in ('EXCERPT = make_prompt()', 'EXCERPT = "one"\nEXCERPT = "two"', 'if True:\n EXCERPT = "nested"', 'EXCERPT = f"{value}"', 'broken = ('):
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.literal_assignment(source, "EXCERPT")

    def test_partial_original_unavailable_and_complete_hash_records_are_distinct(self):
        excerpt = EXPECTED["archive"]["text"]
        partial = CHECKS.archive_record(excerpt, "partial-excerpt")
        self.assertEqual({field: partial[field] for field in EXPECTED["archive"]}, EXPECTED["archive"])
        full = "Saved wrapper\n" + excerpt + "\nSaved footer"
        digest = hashlib.sha256(full.encode()).hexdigest()
        exact = CHECKS.archive_record(full, "hash-verified-reconstruction", expected_hash=digest, complete=True)
        self.assertEqual(exact, {"kind": "hash-verified-reconstruction", "text": full, "sha256": digest, "complete": True})
        self.assertEqual(CHECKS.archive_record(full, "complete-original", complete=True)["text"], full)
        self.assertEqual(CHECKS.archive_record(None, "unavailable"), {"kind": "unavailable", "text": None, "sha256": None, "complete": False})

    def test_false_exact_archive_prefix_hash_later_substitution_and_missing_wrapper_fail(self):
        excerpt = EXPECTED["archive"]["text"]
        digest = hashlib.sha256(excerpt.encode()).hexdigest()
        for action in (lambda: CHECKS.archive_record(excerpt, "complete-original"),
                       lambda: CHECKS.archive_record(excerpt, "hash-verified-reconstruction", digest, False),
                       lambda: CHECKS.archive_record(excerpt, "hash-verified-reconstruction", digest[:12], True),
                       lambda: CHECKS.archive_record(excerpt + " later wording", "hash-verified-reconstruction", digest, True),
                       lambda: CHECKS.archive_record(excerpt, "hash-verified-reconstruction", complete=True),
                       lambda: CHECKS.archive_record("Later template", "unavailable"),
                       lambda: CHECKS.archive_record(excerpt, "partial-excerpt", complete=True)):
            with self.assertRaises(CHECKS.ReportCheckError):
                action()


class DiagramTests(FixtureCase):
    def test_existing_diagram_renderer_regenerates_asset_and_source_identity(self):
        graph = json.loads((self.root / "diagrams/workflow.json").read_text())
        reordered = deepcopy(graph)
        reordered["nodes"].reverse()
        (self.root / "diagrams/workflow.json").write_text(json.dumps(reordered))
        manifest = json.loads((self.root / "diagrams/manifest.json").read_text())
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.checked_asset(self.root, manifest)
        mapping = json.loads((self.root / "build.json").read_text())
        command = [sys.executable, *mapping["regenerate_argv"][1:]]
        result = subprocess.run(command, cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["status"], "completed")
        refreshed = json.loads((self.root / "diagrams/manifest.json").read_text())
        self.assertEqual(refreshed["source"]["sha256"], hashlib.sha256((self.root / "diagrams/workflow.json").read_bytes()).hexdigest())
        svg = CHECKS.checked_asset(self.root, refreshed)
        CHECKS.verify_diagram(graph, reordered)
        for label in ("Yes", "No", "loop", "optional"):
            self.assertIn(label, svg)
        CHECKS.namespace_svg(svg, "regenerated")

    def test_authoritative_graph_decisions_loops_optional_connections_and_labels_preserved(self):
        graph = json.loads((self.root / "diagrams/workflow.json").read_text())
        reordered = {"nodes": list(reversed(graph["nodes"])), "edges": list(reversed(graph["edges"]))}
        CHECKS.verify_diagram(graph, reordered)
        for index, edge in enumerate(graph["edges"]):
            with self.subTest(kind=edge["kind"]):
                candidate = deepcopy(graph)
                del candidate["edges"][index]
                self.rejected("lost-diagram-decision", lambda: CHECKS.verify_diagram(graph, candidate))
        candidate = deepcopy(graph)
        candidate["nodes"][0]["label"] = "Changed meaning"
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.verify_diagram(graph, candidate)

    def test_source_and_asset_hashes_are_both_verified(self):
        manifest = json.loads((self.root / "diagrams/manifest.json").read_text())
        self.assertEqual(CHECKS.checked_asset(self.root, manifest), (self.root / "diagrams/workflow.svg").read_text())
        for field in ("source", "asset"):
            modified = deepcopy(manifest)
            modified[field]["sha256"] = "0" * 64
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.checked_asset(self.root, modified)

    def test_svg_namespaces_keep_local_references_and_meaningful_accessibility_text(self):
        svg = (self.root / "diagrams/workflow.svg").read_text()
        svg = svg.replace('</svg>', '<use href="#node-saved"/><g aria-labelledby="title" aria-describedby="description"/></svg>')
        transformed = CHECKS.namespace_svg(svg, "reference-chart")
        root = ET.fromstring(transformed)
        identifiers = {element.get("id") for element in root.iter() if element.get("id")}
        self.assertTrue(all(identity.startswith("reference-chart") for identity in identifiers))
        self.assertIn('href="#reference-chart-node-saved"', transformed)
        self.assertIn('url(#reference-chart-arrow)', transformed)
        self.assertEqual(root.get("role"), "img")
        self.assertIn(root.get("aria-labelledby"), identifiers)
        self.assertIn(root.get("aria-describedby"), identifiers)
        self.assertIn("Yes and No decision branches", transformed)

    def test_svg_active_external_missing_titles_and_broken_references_fail(self):
        svg = (self.root / "diagrams/workflow.svg").read_text()
        for mutation in ('<script>alert(1)</script>', '<foreignObject><p>active</p></foreignObject>',
                         '<use href="https://example.invalid/a.svg#id"/>', '<image href="private.png"/>',
                         '<g onload="alert(1)"/>', '<use href="#absent"/>',
                         '<style>body{display:none}</style>', '<style>#node-saved{fill:image-set("private.png" 1x)}</style>'):
            with self.subTest(mutation=mutation), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.namespace_svg(svg.replace('</svg>', mutation + '</svg>'), "chart")
        for transformed in (svg.replace('<title id="title">Saved decision workflow</title>', ''),
                            '<!DOCTYPE svg [<!ENTITY evil SYSTEM "private.txt">]>' + svg):
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.namespace_svg(transformed, "chart")

    def test_css_compound_selector_is_rewritten_or_rejected_and_literal_attribute_selector_preserved_or_rejected(self):
        svg = (self.root / "diagrams/workflow.svg").read_text()
        for css, required in (('#node-saved.box{fill:red}', '#chart-node-saved.box'),
                              ("[fill='#fff']{stroke:red}", "[fill='#fff']")):
            try:
                transformed = CHECKS.namespace_svg(svg.replace('</svg>', '<style>' + css + '</style></svg>'), "chart")
            except CHECKS.ReportCheckError:
                continue
            self.assertIn(required, transformed)


class HTMLAndVerificationTests(unittest.TestCase):
    def test_observed_failures_and_blockers_cannot_be_omitted(self):
        for status in ("failed", "blocked", "not-run"):
            with self.subTest(status=status), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.verification_claims({}, {"mapped-check": {"status": status, "evidence": "actual check record"}})

    def test_local_links_anchors_print_css_and_approved_hash_pinned_script(self):
        script = 'document.documentElement.dataset.checked="true";'
        content = '<style>@media print{p{color:black}}@page{margin:1cm}</style><p id="saved">Saved</p><a href="#saved">Local</a><script>' + script + '</script>'
        result = CHECKS.inspect_html(content, (hashlib.sha256(script.encode()).hexdigest(),))
        self.assertEqual(result["status"], "completed")
        self.assertTrue(result["evidence"])
        self.assertNotIn("browser completed", result["evidence"])
        with self.assertRaises(CHECKS.ReportCheckError):
            CHECKS.inspect_html(content)

    def test_duplicate_anchors_broken_links_external_or_active_content_and_unknown_data_scripts_fail(self):
        for content in ('<p id="same"></p><p id="same"></p>', '<a href="#missing">Missing</a>',
                        CASES["external-script"]["mutation"]["html"], '<script>unknown()</script>',
                        '<script type="application/json">{"count":5}</script>', '<style>@import "private.css";</style>',
                        '<style>p{background:image-set("private.png" 1x)}</style>', '<p onclick="active()">text</p>',
                        '<iframe src="private.html"></iframe>', '<a href="javascript:active()">active</a>',
                        '<img src="https://example.invalid/image.png">', '<script>unterminated'):
            with self.subTest(content=content), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.inspect_html(content)

    def test_verification_has_distinct_observed_outcomes_and_no_false_completion(self):
        observed = {name: {"status": name, "evidence": "actual recorded outcome" if name != "not-run" else None}
                    for name in ("completed", "failed", "blocked", "not-run")}
        CHECKS.verification_claims({name: name for name in observed}, observed)
        for claimed, actual in (({"visual": "completed"}, {}),
                               ({"visual": "completed"}, {"visual": {"status": "not-run", "evidence": None}}),
                               ({"visual": "completed"}, {"visual": {"status": "completed", "evidence": None}}),
                               ({"visual": "completed"}, {"visual": {"status": "completed", "result": "fail", "evidence": "actual failure"}}),
                               ({"visual": "success"}, {})):
            with self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.verification_claims(claimed, actual)


class TransactionalTests(FixtureCase):
    def test_cooperative_lock_blocks_competing_writer_without_replacing_report(self):
        previous = (self.root / "report.html").read_bytes()
        lock = self.root / ".report.html.report-lock"
        lock.mkdir()
        with self.assertRaises(CHECKS.ReportCheckError):
            self.build(lambda staged: staged.write_text("candidate"))
        self.assertEqual((self.root / "report.html").read_bytes(), previous)
        self.assertTrue(lock.is_dir())

    def build(self, callback, checks=()):
        return CHECKS.transactional_build(self.root, ["presentation.json", "templates/report.html"], "report.html", callback, checks)

    def test_success_commits_only_after_actual_check_and_source_hash_verification(self):
        previous = (self.root / "report.html").read_bytes()
        seen = []
        def check(staged):
            self.assertEqual((self.root / "report.html").read_bytes(), previous)
            self.assertEqual(staged.read_text(), "new staged report")
            seen.append(staged)
            return {"status": "completed", "evidence": "actually checked staged bytes"}
        result = self.build(lambda staged: staged.write_text("new staged report"), [check])
        self.assertEqual(result["status"], "completed")
        self.assertEqual((self.root / "report.html").read_text(), "new staged report")
        self.assertEqual(result["output_sha256"], hashlib.sha256(b"new staged report").hexdigest())
        self.assertEqual(result["source_hashes"]["presentation.json"], hashlib.sha256((self.root / "presentation.json").read_bytes()).hexdigest())
        self.assertEqual(len(seen), 1)
        self.assertEqual(list(self.root.glob(".report-stage-*")), [])

    def test_build_exception_empty_stage_or_actual_check_failure_preserves_prior(self):
        previous = (self.root / "report.html").read_bytes()
        def failing(staged):
            staged.write_text("partial")
            raise RuntimeError("synthetic failure")
        with self.assertRaises(RuntimeError):
            self.build(failing)
        for outcome in (False, {"status": "failed"}, {"status": "blocked"}, {"status": "not-run"},
                        {"status": "completed", "result": "fail", "evidence": "failed"}):
            with self.subTest(outcome=outcome), self.assertRaises(CHECKS.ReportCheckError):
                self.build(lambda staged: staged.write_text("candidate"), [lambda staged: outcome])
            self.assertEqual((self.root / "report.html").read_bytes(), previous)
        with self.assertRaises(CHECKS.ReportCheckError):
            self.build(lambda staged: None)
        self.assertEqual((self.root / "report.html").read_bytes(), previous)

    def test_check_exception_preserves_previous_report(self):
        previous = (self.root / "report.html").read_bytes()
        def check(staged):
            raise RuntimeError("failed checker")
        with self.assertRaises(RuntimeError):
            self.build(lambda staged: staged.write_text("candidate"), [check])
        self.assertEqual((self.root / "report.html").read_bytes(), previous)

    def test_destructive_writer_is_rejected_and_prior_report_restored(self):
        previous = (self.root / "report.html").read_bytes()
        def destructive(staged):
            (self.root / "report.html").write_text("destructive live output")
            staged.write_text("candidate")
        self.rejected("destructive-rebuild", lambda: self.build(destructive))
        self.assertEqual((self.root / "report.html").read_bytes(), previous)

    def test_concurrent_source_edit_is_preserved_while_prior_report_remains_intact(self):
        previous = (self.root / "report.html").read_bytes()
        def concurrent(staged):
            staged.write_text("candidate")
            (self.root / "presentation.json").write_text("concurrent source edit")
        self.rejected("concurrent-source", lambda: self.build(concurrent))
        self.assertEqual((self.root / "report.html").read_bytes(), previous)
        self.assertEqual((self.root / "presentation.json").read_text(), "concurrent source edit")

    def test_unrelated_concurrent_output_edit_during_checks_is_preserved_not_rolled_back(self):
        def unrelated_editor(staged):
            (self.root / "report.html").write_text("newer unrelated editor output")
            return {"status": "completed", "evidence": "checked stage while an unrelated editor saved"}
        self.rejected("concurrent-output", lambda: self.build(lambda staged: staged.write_text("candidate"), [unrelated_editor]))
        self.assertEqual((self.root / "report.html").read_text(), "newer unrelated editor output")

    def test_checker_stage_symlink_truncation_or_mutation_cannot_commit_as_completed(self):
        previous = (self.root / "report.html").read_bytes()
        external = Path(self.temporary.name) / "outside.html"
        external.write_text("external bytes")
        def symlink(staged):
            staged.unlink()
            staged.symlink_to(external)
            return {"status": "completed", "evidence": "false acceptance"}
        def truncate(staged):
            staged.write_text("")
            return {"status": "completed", "evidence": "false acceptance"}
        def mutate(staged):
            staged.write_text("changed after validation")
            return {"status": "completed", "evidence": "false acceptance"}
        for check in (symlink, truncate, mutate):
            with self.subTest(check=check.__name__), self.assertRaises(CHECKS.ReportCheckError):
                self.build(lambda staged: staged.write_text("candidate"), [check])
            self.assertEqual((self.root / "report.html").read_bytes(), previous)
            self.assertEqual(external.read_text(), "external bytes")

    def test_builder_live_output_symlink_then_failure_restores_prior_without_external_write(self):
        previous = (self.root / "report.html").read_bytes()
        external = Path(self.temporary.name) / "outside.html"
        external.write_text("external bytes")
        def destructive(staged):
            (self.root / "report.html").unlink()
            (self.root / "report.html").symlink_to(external)
            raise RuntimeError("destructive writer failure")
        with self.assertRaises((RuntimeError, CHECKS.ReportCheckError)):
            self.build(destructive)
        self.assertFalse((self.root / "report.html").is_symlink())
        self.assertEqual((self.root / "report.html").read_bytes(), previous)
        self.assertEqual(external.read_text(), "external bytes")

    def test_initial_creation_failure_keeps_sources_and_creates_no_report(self):
        (self.root / "report.html").unlink()
        source = (self.root / "presentation.json").read_bytes()
        def fail(staged):
            staged.write_text("partial")
            raise RuntimeError("creation failed")
        with self.assertRaises(RuntimeError):
            self.build(fail)
        self.assertFalse((self.root / "report.html").exists())
        self.assertEqual((self.root / "presentation.json").read_bytes(), source)

    def test_inputs_outputs_and_assets_reject_symlink_traversal_absolute_and_directory_paths(self):
        external = Path(self.temporary.name) / "external"
        external.mkdir()
        (external / "source.json").write_text("{}")
        (self.root / "linked").symlink_to(external, target_is_directory=True)
        for sources, output in ((["linked/source.json"], "report.html"), (["../outside.json"], "report.html"),
                                ([str(self.root / "presentation.json")], "report.html"), (["presentation.json"], "linked/report.html"),
                                (["evidence"], "report.html"), (["presentation.json"], "../report.html")):
            with self.subTest(sources=sources, output=output), self.assertRaises(CHECKS.ReportCheckError):
                CHECKS.transactional_build(self.root, sources, output, lambda staged: staged.write_text("candidate"))
        self.assertFalse((external / "report.html").exists())


if __name__ == "__main__":
    unittest.main()
