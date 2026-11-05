import hashlib
import json
from pathlib import Path
import re
import sys
import types
import unittest
from unittest.mock import patch

from scripts.build_skills import ROOT, payload


DIRECTORY = ROOT / "evaluations/workflow-methods"


def load_json(relative):
    return json.loads((DIRECTORY / relative).read_text())


def execute_source(source, filename):
    namespace = {}
    exec(compile(source, filename, "exec"), namespace)
    return namespace


def python_blocks(relative):
    return re.findall(r"```python\n(.*?)\n```", (ROOT / relative).read_text(), re.S)


class RecordingQueue:
    def __init__(self):
        self.identities = []

    def submit(self, identity):
        self.identities.append(identity)
        return {"status": "submitted", "id": identity}


def failing_write(unused_value):
    raise OSError("synthetic persistence failure")


class WorkflowMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {case["id"]: case for case in load_json("cases.json")["cases"]}
        cls.expected = load_json("expected.json")

    def test_frozen_current_instruction_snapshot_has_verifiable_content(self):
        baseline = load_json("baseline.json")
        self.assertEqual(baseline["kind"], "synthetic_public_instruction_snapshot")
        for relative, record in baseline["sources"].items():
            with self.subTest(source=relative):
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn("..", Path(relative).parts)
                self.assertEqual(hashlib.sha256(record["content"].encode()).hexdigest(), record["sha256"])
        modes = ["develop/" + name + ".md" for name in ["bdd", "prd", "prompt", "backlog"]]
        modes += ["review/" + name + ".md" for name in ["code", "smells"]]
        self.assertTrue(set(modes).issubset(baseline["sources"]))

    def test_raw_cases_do_not_receive_evaluator_answers(self):
        self.assertTrue(self.expected["evaluator_only"])
        self.assertTrue(self.expected["illustrative_not_agent_outputs"])
        self.assertEqual(set(self.cases), set(self.expected["cases"]))
        for case in self.cases.values():
            self.assertEqual(set(case), {"id", "request", "context", "artifacts"})
            for relative in case["artifacts"]:
                self.assertFalse(Path(relative).is_absolute())
                self.assertNotIn("..", Path(relative).parts)
                self.assertNotIn("expected", relative)

    def test_worked_review_verifies_actual_original_and_revised_sources(self):
        blocks = python_blocks("review/code-worked.md")
        original = execute_source(blocks[1], "worked/original_importer.py")
        revised = execute_source(blocks[3], "worked/revised_importer.py")
        order = {"id": "order-7", "label": "Restock"}
        queue = RecordingQueue()
        original["submit_by_label"]("Restock", [order], queue)
        self.assertEqual(queue.identities, ["Restock"])
        for label, orders, status, identities in [
            (" RESTOCK ", [order], "submitted", ["order-7"]),
            ("Restock", [order, dict(order)], "submitted", ["order-7"]),
            ("Missing", [order], "not_found", []),
            ("Restock", [order, {"id": "order-8", "label": "restock"}], "ambiguous", []),
        ]:
            with self.subTest(status=status, orders=orders):
                queue = RecordingQueue()
                result = revised["submit_by_label"](label, orders, queue)
                self.assertEqual(result["status"], status)
                self.assertEqual(queue.identities, identities)
        queue = RecordingQueue()
        revised["submit_order"]("order-direct", queue)
        self.assertEqual(queue.identities, ["order-direct"])
        with self.assertRaises(OSError):
            revised["submit_by_label"]("Restock", [order], types.SimpleNamespace(submit=failing_write))

    def test_worked_audit_reproduces_terminal_omission_and_field_ownership(self):
        blocks = python_blocks("review/smells-worked.md")
        policies = execute_source(blocks[0], "worked/retries.py")
        events = execute_source(blocks[1], "worked/events.py")
        for name in ["normal_run", "validated_run"]:
            for attempt in [0, 1]:
                with self.subTest(policy=name, attempt=attempt):
                    observed = []
                    self.assertEqual(policies[name](attempt, observed.append), "retry")
                    self.assertEqual(observed, [])
        normal_events = []
        validated_events = []
        self.assertEqual(policies["normal_run"](2, normal_events.append), "failed")
        self.assertEqual(policies["validated_run"](2, validated_events.append), "failed")
        self.assertEqual(normal_events, ["terminal"])
        self.assertEqual(validated_events, [])
        source = {"processed_at": "2026-11-04T12:00:00Z", "issued_on": "2026-10-01"}
        for name, expected_index, expected_timestamp in [
            ("emit_ok", 9, source["processed_at"]),
            ("emit_failed", 10, source["issued_on"]),
        ]:
            state = {"id": "synthetic-run", "next_index": 9}
            with self.assertRaises(OSError):
                events[name](state, source, failing_write)
            self.assertEqual(state["next_index"], expected_index)
            rows = []
            state = {"id": "synthetic-run", "next_index": 9}
            events[name](state, source, rows.append)
            self.assertEqual(rows[0]["recorded_at"], expected_timestamp)
            self.assertEqual(set(rows[0]), {"run_id", "index", "recorded_at", "status"})
            self.assertEqual(state["next_index"], 10)

    def test_worked_configuration_consequence_and_preserved_precedence_are_real(self):
        blocks = python_blocks("review/smells-worked.md")
        fields = types.ModuleType("fields")
        exec(compile(blocks[2], "worked/fields.py", "exec"), fields.__dict__)
        with patch.dict(sys.modules, {"fields": fields}):
            config = execute_source(blocks[3], "worked/config.py")
        render = execute_source(blocks[4], "worked/render.py")
        self.assertEqual(config["load_config"]({}, {})["timeout_seconds"], 15)
        self.assertEqual(render["render_environment"]({})["APP_TIMEOUT"], "30")
        self.assertEqual(config["load_config"]({"timeout_seconds": 22}, {"APP_TIMEOUT": 18})["timeout_seconds"], 22)
        for values in [{"unknown": 1}, {"timeout_seconds": 0}]:
            with self.assertRaises(ValueError):
                config["load_config"](values, {})

    def test_held_out_revised_review_resolves_identity_but_not_ambiguity(self):
        artifacts = self.cases["workflow-revised-code"]["artifacts"]
        baseline = execute_source(artifacts["baseline.py"], "heldout/baseline.py")
        candidate = execute_source(artifacts["catalog.py"], "heldout/catalog.py")
        first = {"sku": "sku-17", "title": "Spare kit"}
        second = {"sku": "sku-29", "title": "SPARE KIT"}
        written = []
        baseline["choose"]("Spare kit", [first], written.append)
        self.assertEqual(written, ["Spare kit"])
        written.clear()
        candidate["choose"](" SPARE KIT ", [first], written.append)
        self.assertEqual(written, ["sku-17"])
        for products, selected in [([first, second], "sku-17"), ([second, first], "sku-29")]:
            written.clear()
            candidate["choose"]("Spare kit", products, written.append)
            self.assertEqual(written, [selected])
        previous = {entry["id"] for entry in json.loads(artifacts["prior.json"])}
        dispositions = self.expected["cases"]["workflow-revised-code"]["prior_dispositions"]
        self.assertEqual(previous, set(dispositions))
        self.assertEqual(dispositions["P01"], "resolved")
        self.assertEqual(dispositions["P02"], "open")
        self.assertIn("submit_sku", artifacts["client.py"])

    def test_held_out_audit_demonstrates_each_supported_consequence(self):
        artifacts = self.cases["workflow-structural-audit"]["artifacts"]
        policies = execute_source(artifacts["policies.py"], "heldout/policies.py")
        traces = {}
        for name in ["legacy", "checked"]:
            traces[name] = []
            self.assertEqual(policies[name](4, traces[name].append), "done")
        self.assertEqual(traces, {"legacy": ["terminal"], "checked": []})
        journal = execute_source(artifacts["journal.py"], "heldout/journal.py")
        document = {"processed_at": "2026-11-04T09:00:00Z", "published_on": "2025-12-31"}
        for producer, cursor in [("accepted", 4), ("rejected", 5)]:
            state = {"cursor": 4}
            with self.assertRaises(OSError):
                journal[producer](state, document, failing_write)
            self.assertEqual(state["cursor"], cursor)
        settings = execute_source(artifacts["settings.py"], "heldout/settings.py")
        deployment = execute_source(artifacts["deploy.py"], "heldout/deploy.py")
        self.assertEqual(settings["runtime"]({}, {})["batch_size"], 40)
        self.assertEqual(deployment["deployment"]({})["BATCH_SIZE"], "60")
        coverage = self.expected["cases"]["workflow-structural-audit"]["coverage"]
        self.assertEqual(set(coverage), set(artifacts) | {"transport.py"})
        self.assertTrue(coverage["transport.py"].startswith("Unreviewed"))

    def test_all_finding_locations_exist_in_the_raw_held_out_snapshot(self):
        for identity, expected in self.expected["cases"].items():
            artifacts = self.cases[identity]["artifacts"]
            for finding in expected["findings"]:
                locations = finding.get("locations", [finding.get("location")])
                for location in locations:
                    relative, line = location.split(":")
                    self.assertIn(relative, artifacts)
                    self.assertLessEqual(int(line), len(artifacts[relative].splitlines()))
                    self.assertTrue(artifacts[relative].splitlines()[int(line) - 1].strip())

    def test_complete_worked_resources_export_but_evaluator_material_does_not(self):
        inventory, exported, inputs = payload(ROOT)
        for parent, names in [("develop", ["bdd", "prd", "prompt", "backlog"]),
                              ("review", ["code", "smells"])]:
            for name in names:
                relative = name + "-worked.md"
                self.assertIn(relative, inventory["owned_resources"][parent])
                self.assertEqual(exported["skills/" + parent + "/" + relative], (ROOT / parent / relative).read_bytes())
        self.assertFalse(any("evaluations/" in relative for relative in inputs))
        self.assertFalse(any("evaluations/" in relative or relative.endswith("/work.md") for relative in exported))

    def test_focused_traceability_has_real_instruction_case_and_check_paths(self):
        traceability = load_json("traceability.json")
        self.assertEqual(set(traceability["scope"]), {
            "develop bdd", "develop prd", "develop prompt", "develop backlog",
            "review code", "review smells",
        })
        for requirement in traceability["requirements"]:
            with self.subTest(requirement=requirement["id"]):
                self.assertTrue(requirement["supplied_requirements"])
                self.assertIn(requirement["disposition"], {"retained", "generalized", "excluded"})
                for relative in requirement["instruction_or_reference"] + requirement["worked_case"]:
                    current = ROOT / relative.replace("/references/", "/")
                    self.assertTrue(current.is_file(), relative)
                for module in requirement["verification_modules"]:
                    self.assertTrue((ROOT / (module.replace(".", "/") + ".py")).is_file(), module)
        for relative in traceability["case_sets"]:
            self.assertTrue((DIRECTORY / relative).is_file(), relative)

    def test_frozen_inputs_and_criteria_are_unchanged_and_separately_scoped(self):
        freeze = load_json("freeze.json")
        for relative, checksum in freeze["corpus_hashes"].items():
            self.assertEqual(hashlib.sha256((DIRECTORY / relative).read_bytes()).hexdigest(), checksum)
        self.assertIn("baseline.json", freeze["corpus_hashes"])
        self.assertEqual(freeze["model_protocol_approval"], "pending")
        for prefix in ["", "bdd-prd/", "prompt-backlog/"]:
            inputs = load_json(prefix + "cases.json")
            criteria = load_json(prefix + "expected.json")
            self.assertTrue(inputs["synthetic_only"])
            self.assertTrue(criteria["evaluator_only"])
            self.assertEqual({case["id"] for case in inputs["cases"]}, set(criteria["cases"]))
            for case in inputs["cases"]:
                self.assertEqual(set(case), {"id", "request", "context", "artifacts"})

    def test_results_do_not_claim_unperformed_model_quality(self):
        results = load_json("results.json")
        for name in ["paired_model_execution", "generation_quality", "real_host_invocation", "historical_reference_fidelity"]:
            self.assertEqual(results[name]["status"], "not_run")
        self.assertFalse(results["full_method_quality_acceptance"])


if __name__ == "__main__":
    unittest.main()
